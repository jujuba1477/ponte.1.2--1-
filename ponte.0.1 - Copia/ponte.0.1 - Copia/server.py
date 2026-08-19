from __future__ import annotations

import json
import mimetypes
import os
import re
import socket
import sqlite3
import sys
import threading
import uuid
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None
    DictCursor = None


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
PORT_FILE = ROOT / ".server.port"
SCHEMA_LOCK = threading.Lock()
SCHEMA_READY = False
DATABASE_BACKEND = ""
DATABASE_WARNING = ""


def load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def parse_port(value: str, name: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} precisa ser um numero. Valor atual: {value!r}.") from error

    if not 1 <= port <= 65535:
        raise RuntimeError(f"{name} precisa ficar entre 1 e 65535. Valor atual: {port}.")

    return port


def env_port(name: str, default: str) -> int:
    return parse_port(env(name, default), name)


def env_bool(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() not in {"0", "false", "nao", "não", "no", "off"}


def browser_host(host: str) -> str:
    if host in {"", "0.0.0.0", "::"}:
        return "127.0.0.1"

    return host


def is_address_in_use(error: OSError) -> bool:
    return (
        getattr(error, "errno", None) in {48, 98, 10048}
        or getattr(error, "winerror", None) == 10048
        or "address already in use" in str(error).lower()
        or "normalmente é permitida apenas uma utilização" in str(error).lower()
    )


def bind_server(host: str, preferred_port: int) -> tuple[ThreadingHTTPServer, int]:
    for port in range(preferred_port, preferred_port + 20):
        try:
            server = ThreadingHTTPServer((host, port), PonteHandler)
            return server, port
        except OSError as error:
            if is_address_in_use(error):
                continue

            raise

    raise RuntimeError(
        f"Nao encontrei uma porta livre entre {preferred_port} e {preferred_port + 19}."
    )


def write_port_file(port: int) -> None:
    try:
        PORT_FILE.write_text(str(port), encoding="utf-8")
    except OSError as error:
        print(f"Aviso: nao consegui atualizar {PORT_FILE.name}: {error}")


def open_browser(url: str) -> None:
    if not env_bool("OPEN_BROWSER", True):
        return

    threading.Timer(0.6, lambda: webbrowser.open(url)).start()


def mysql_config(database: str | None = None) -> dict:
    config = {
        "host": env("MYSQL_HOST", "127.0.0.1"),
        "port": env_port("MYSQL_PORT", "3306"),
        "user": env("MYSQL_USER", "root"),
        "password": env("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }

    if database:
        config["database"] = database

    return config


def mysql_database_name() -> str:
    name = env("MYSQL_DATABASE", "ponte_esperanca")

    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise RuntimeError("MYSQL_DATABASE deve conter apenas letras, numeros e underscore.")

    return name


def database_driver() -> str:
    driver = env("DB_DRIVER", "auto").strip().lower()

    if driver not in {"auto", "mysql", "sqlite"}:
        raise RuntimeError("DB_DRIVER deve ser auto, mysql ou sqlite.")

    return driver


def require_mysql_backend() -> bool:
    return env_bool("DB_REQUIRE_MYSQL", False)


def sqlite_database_path() -> Path:
    configured_path = env("SQLITE_DATABASE", "ponte_esperanca.sqlite3")
    path = Path(configured_path)

    if not path.is_absolute():
        path = ROOT / path

    return path


def get_sqlite_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(sqlite_database_path())
    connection.row_factory = sqlite3.Row
    return connection


def require_mysql_driver() -> None:
    if pymysql is None:
        raise RuntimeError(
            "PyMySQL nao esta instalado neste Python. Rode iniciar-servidor.bat para "
            "criar o .venv do projeto e instalar as dependencias."
        )


def get_connection(database: str | None = None):
    require_mysql_driver()
    assert pymysql is not None

    try:
        return pymysql.connect(**mysql_config(database))
    except Exception as error:
        raise RuntimeError(build_mysql_error_message(error)) from error


def build_mysql_error_message(error: Exception) -> str:
    raw_message = str(error)
    error_code = error.args[0] if getattr(error, "args", None) else None
    user = env("MYSQL_USER", "root")
    host = env("MYSQL_HOST", "127.0.0.1")
    port = env("MYSQL_PORT", "3306")
    database = env("MYSQL_DATABASE", "ponte_esperanca")

    if error_code == 1045 or "1045" in raw_message or "Access denied for user" in raw_message:
        return (
            "MySQL recusou o login. Edite o arquivo .env e preencha MYSQL_USER "
            "e MYSQL_PASSWORD com as credenciais corretas. "
            f"Tentativa atual: usuario '{user}' em {host}:{port}. "
            "Se voce usa MySQL Workbench, use o mesmo usuario e senha dele."
        )

    if error_code == 1044 or "1044" in raw_message:
        return (
            f"O usuario '{user}' conectou, mas nao tem permissao para acessar ou criar "
            f"o banco '{database}'. Ajuste MYSQL_DATABASE no .env ou conceda permissao "
            "a esse usuario no MySQL."
        )

    if error_code == 1049 or "1049" in raw_message or "Unknown database" in raw_message:
        return (
            f"O banco '{database}' nao existe e nao consegui cria-lo automaticamente. "
            "Crie o banco no MySQL Workbench ou use um usuario com permissao de CREATE."
        )

    if error_code == 1146 or "1146" in raw_message:
        return (
            "Uma tabela esperada nao existe no banco. Acesse /api/health para forcar "
            "a recriacao do schema ou reinicie o servidor."
        )

    if error_code in {2002, 2003} or "2003" in raw_message or "Can't connect" in raw_message:
        return (
            "Nao consegui conectar ao MySQL. Confirme se o servico MySQL80 esta rodando "
            f"e se MYSQL_HOST={host} e MYSQL_PORT={port} estao corretos no .env."
        )

    return raw_message


def column_exists(cursor, database: str, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (database, table, column),
    )
    return bool(cursor.fetchone()["total"])


def ensure_column(
    cursor,
    database: str,
    table: str,
    column: str,
    definition: str,
    after: str | None = None,
) -> None:
    if column_exists(cursor, database, table, column):
        return

    after_sql = f" AFTER `{after}`" if after and column_exists(cursor, database, table, after) else ""
    cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}{after_sql}")


def sync_legacy_columns(cursor, database: str) -> None:
    if column_exists(cursor, database, "item_donations", "tipoItem"):
        cursor.execute(
            """
            UPDATE item_donations
            SET tipo_item = tipoItem
            WHERE (tipo_item IS NULL OR tipo_item = '')
              AND tipoItem IS NOT NULL
              AND tipoItem <> ''
            """
        )


def ensure_uuid_values(cursor, table: str) -> None:
    cursor.execute(f"UPDATE `{table}` SET uuid = UUID() WHERE uuid IS NULL OR uuid = ''")


def migrate_schema(cursor, database: str) -> None:
    ensure_column(cursor, database, "contacts", "uuid", "CHAR(36) NULL", "id")
    ensure_column(cursor, database, "contacts", "nome", "VARCHAR(150) NULL", "uuid")
    ensure_column(cursor, database, "contacts", "email", "VARCHAR(190) NULL", "nome")
    ensure_column(cursor, database, "contacts", "mensagem", "TEXT NULL", "email")
    ensure_column(
        cursor,
        database,
        "contacts",
        "created_at",
        "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "mensagem",
    )

    ensure_column(cursor, database, "item_donations", "uuid", "CHAR(36) NULL", "id")
    ensure_column(cursor, database, "item_donations", "nome", "VARCHAR(150) NULL", "uuid")
    ensure_column(
        cursor,
        database,
        "item_donations",
        "telefone",
        "VARCHAR(40) NULL",
        "nome",
    )
    ensure_column(
        cursor,
        database,
        "item_donations",
        "tipo_item",
        "VARCHAR(120) NULL",
        "telefone",
    )
    ensure_column(cursor, database, "item_donations", "detalhes", "TEXT NULL", "tipo_item")
    ensure_column(
        cursor,
        database,
        "item_donations",
        "created_at",
        "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "detalhes",
    )
    sync_legacy_columns(cursor, database)

    ensure_column(cursor, database, "volunteers", "uuid", "CHAR(36) NULL", "id")
    ensure_column(
        cursor,
        database,
        "volunteers",
        "tipo",
        "VARCHAR(80) NULL DEFAULT 'volunteer'",
        "uuid",
    )
    ensure_column(
        cursor,
        database,
        "volunteers",
        "created_at",
        "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "tipo",
    )

    for table in ("contacts", "item_donations", "volunteers"):
        ensure_uuid_values(cursor, table)


def ensure_mysql_schema() -> None:
    database = mysql_database_name()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            except Exception as error:
                try:
                    with get_connection(database):
                        pass
                except Exception as access_error:
                    raise RuntimeError(build_mysql_error_message(access_error)) from error

    with get_connection(database) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  uuid CHAR(36) NOT NULL UNIQUE,
                  nome VARCHAR(150) NOT NULL,
                  email VARCHAR(190) NOT NULL,
                  mensagem TEXT NOT NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS item_donations (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  uuid CHAR(36) NOT NULL UNIQUE,
                  nome VARCHAR(150) NOT NULL,
                  telefone VARCHAR(40) NOT NULL,
                  tipo_item VARCHAR(120) NOT NULL,
                  detalhes TEXT NOT NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS volunteers (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  uuid CHAR(36) NOT NULL UNIQUE,
                  tipo VARCHAR(80) NOT NULL DEFAULT 'volunteer',
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            migrate_schema(cursor, database)


def ensure_sqlite_schema() -> None:
    with get_sqlite_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              uuid TEXT NOT NULL UNIQUE,
              nome TEXT NOT NULL,
              email TEXT NOT NULL,
              mensagem TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS item_donations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              uuid TEXT NOT NULL UNIQUE,
              nome TEXT NOT NULL,
              telefone TEXT NOT NULL,
              tipo_item TEXT NOT NULL,
              detalhes TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              uuid TEXT NOT NULL UNIQUE,
              tipo TEXT NOT NULL DEFAULT 'volunteer',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def ensure_schema(force: bool = False) -> None:
    global DATABASE_BACKEND, DATABASE_WARNING, SCHEMA_READY

    if SCHEMA_READY and not force:
        return

    with SCHEMA_LOCK:
        if SCHEMA_READY and not force:
            return

        driver = database_driver()
        DATABASE_WARNING = ""

        if driver == "sqlite":
            ensure_sqlite_schema()
            DATABASE_BACKEND = "sqlite"
            SCHEMA_READY = True
            return

        try:
            ensure_mysql_schema()
            DATABASE_BACKEND = "mysql"
        except Exception as error:
            if require_mysql_backend():
                raise

            ensure_sqlite_schema()
            DATABASE_BACKEND = "sqlite"
            mode_hint = "DB_DRIVER=mysql, mas " if driver == "mysql" else ""
            DATABASE_WARNING = (
                f"{mode_hint}MySQL indisponivel ({error}). Usando SQLite local em "
                f"{sqlite_database_path().name}."
            )

    SCHEMA_READY = True


def insert_contact(payload: dict) -> dict:
    ensure_schema()
    record_uuid = str(uuid.uuid4())
    values = (
        record_uuid,
        payload.get("nome", "").strip(),
        payload.get("email", "").strip(),
        payload.get("mensagem", "").strip(),
    )

    if DATABASE_BACKEND == "sqlite":
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO contacts (uuid, nome, email, mensagem)
                VALUES (?, ?, ?, ?)
                """,
                values,
            )
            connection.commit()
        return {"id": record_uuid}

    with get_connection(mysql_database_name()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO contacts (uuid, nome, email, mensagem)
                VALUES (%s, %s, %s, %s)
                """,
                values,
            )

    return {"id": record_uuid}


def insert_item_donation(payload: dict) -> dict:
    ensure_schema()
    record_uuid = str(uuid.uuid4())
    values = (
        record_uuid,
        payload.get("nome", "").strip(),
        payload.get("telefone", "").strip(),
        (payload.get("itemType") or payload.get("tipoItem", "")).strip(),
        payload.get("detalhes", "").strip(),
    )

    if DATABASE_BACKEND == "sqlite":
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO item_donations (uuid, nome, telefone, tipo_item, detalhes)
                VALUES (?, ?, ?, ?, ?)
                """,
                values,
            )
            connection.commit()
        return {"id": record_uuid}

    with get_connection(mysql_database_name()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO item_donations (uuid, nome, telefone, tipo_item, detalhes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                values,
            )

    return {"id": record_uuid}


def insert_volunteer(payload: dict) -> dict:
    ensure_schema()
    record_uuid = str(uuid.uuid4())
    values = (record_uuid, payload.get("type", "volunteer"))

    if DATABASE_BACKEND == "sqlite":
        with get_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO volunteers (uuid, tipo)
                VALUES (?, ?)
                """,
                values,
            )
            connection.commit()
        return {"id": record_uuid}

    with get_connection(mysql_database_name()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO volunteers (uuid, tipo)
                VALUES (%s, %s)
                """,
                values,
            )

    return {"id": record_uuid}


def validate_required(payload: dict, fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if not str(payload.get(field, "")).strip()]


class PonteHandler(SimpleHTTPRequestHandler):
    server_version = "PonteEsperancaPython/1.0"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        pathname = urlparse(self.path).path

        if pathname == "/api/health":
            self.handle_health()
            return

        if pathname.startswith("/api/"):
            self.send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "error": "Rota de API nao encontrada."},
            )
            return

        self.serve_static(pathname)

    def do_POST(self) -> None:
        pathname = urlparse(self.path).path
        routes = {
            "/api/contact": self.handle_contact,
            "/api/item-donations": self.handle_item_donation,
            "/api/volunteers": self.handle_volunteer,
        }

        handler = routes.get(pathname)

        if handler is None:
            self.send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "error": "Rota de API nao encontrada."},
            )
            return

        try:
            payload = self.read_json()
            handler(payload)
        except ValueError as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})
        except Exception as error:
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": str(error)},
            )

    def handle_health(self) -> None:
        try:
            ensure_schema(force=True)
            database = (
                mysql_database_name()
                if DATABASE_BACKEND == "mysql"
                else sqlite_database_path().name
            )
            payload = {
                "ok": True,
                "service": "Ponte Esperanca API Python",
                "backend": DATABASE_BACKEND,
                "database": database,
            }

            if DATABASE_WARNING:
                payload["warning"] = DATABASE_WARNING

            self.send_json(
                HTTPStatus.OK,
                payload,
            )
        except Exception as error:
            self.send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "ok": False,
                    "service": "Ponte Esperanca API Python",
                    "error": str(error),
                },
            )

    def handle_contact(self, payload: dict) -> None:
        missing = validate_required(payload, ("nome", "email", "mensagem"))

        if missing:
            raise ValueError(f"Campos obrigatorios ausentes: {', '.join(missing)}")

        record = insert_contact(payload)
        self.send_json(HTTPStatus.CREATED, {"ok": True, "record": record})

    def handle_item_donation(self, payload: dict) -> None:
        item_type = payload.get("itemType") or payload.get("tipoItem")
        payload["itemType"] = item_type
        missing = validate_required(payload, ("nome", "telefone", "itemType", "detalhes"))

        if missing:
            raise ValueError(f"Campos obrigatorios ausentes: {', '.join(missing)}")

        record = insert_item_donation(payload)
        self.send_json(HTTPStatus.CREATED, {"ok": True, "record": record})

    def handle_volunteer(self, payload: dict) -> None:
        record = insert_volunteer(payload)
        self.send_json(HTTPStatus.CREATED, {"ok": True, "record": record})

    def read_json(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length invalido.") from error

        if content_length > 1_000_000:
            raise ValueError("Payload muito grande.")

        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as error:
            raise ValueError("JSON invalido.") from error

        if not isinstance(payload, dict):
            raise ValueError("JSON precisa ser um objeto.")

        return payload

    def send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, pathname: str) -> None:
        relative_path = "index.html" if pathname == "/" else unquote(pathname).lstrip("/")
        file_path = (ROOT / relative_path).resolve()

        if ROOT not in file_path.parents and file_path != ROOT:
            self.send_error(HTTPStatus.FORBIDDEN, "Acesso negado.")
            return

        if file_path.is_dir():
            file_path = file_path / "index.html"

        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Arquivo nao encontrado.")
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> int:
    load_env_file()
    host = env("APP_HOST", "127.0.0.1")
    preferred_port = parse_port(
        os.environ.get("APP_PORT") or os.environ.get("PORT") or "3000",
        "APP_PORT",
    )

    try:
        ensure_schema()
        if DATABASE_BACKEND == "sqlite" and DATABASE_WARNING:
            print(f"Aviso: {DATABASE_WARNING}")
    except Exception as error:
        print(f"Aviso: banco de dados ainda nao esta pronto: {error}")

    server, port = bind_server(host, preferred_port)
    url = f"http://{browser_host(host)}:{port}"
    write_port_file(port)

    if port != preferred_port:
        print(f"Aviso: porta {preferred_port} ocupada. Usando porta {port}.")

    print(f"Ponte Esperanca rodando em {url}")
    print(f"API healthcheck em {url}/api/health")
    print("Pressione Ctrl+C para parar.")
    open_browser(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        return 0
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())


from getpass import getpass
import os
from pathlib import Path

import server


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"


def read_env() -> dict[str, str]:
    values = {}

    if not ENV_PATH.exists():
        return values

    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def write_env(values: dict[str, str]) -> None:
    ordered_keys = [
        "APP_HOST",
        "APP_PORT",
        "DB_DRIVER",
        "DB_REQUIRE_MYSQL",
        "SQLITE_DATABASE",
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE",
    ]
    lines = []

    for key in ordered_keys:
        if key in values:
            lines.append(f"{key}={values[key]}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    values = {
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "3000",
        "DB_DRIVER": "auto",
        "DB_REQUIRE_MYSQL": "0",
        "SQLITE_DATABASE": "ponte_esperanca.sqlite3",
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "",
        "MYSQL_DATABASE": "ponte_esperanca",
        **read_env(),
    }

    print("Teste de conexao MySQL da Ponte Esperanca")
    print("Pressione Enter para manter o valor atual.")

    user = input(f"Usuario MySQL [{values['MYSQL_USER']}]: ").strip() or values["MYSQL_USER"]
    host = input(f"Host MySQL [{values['MYSQL_HOST']}]: ").strip() or values["MYSQL_HOST"]
    port_raw = input(f"Porta MySQL [{values['MYSQL_PORT']}]: ").strip() or values["MYSQL_PORT"]
    database = (
        input(f"Banco de dados [{values['MYSQL_DATABASE']}]: ").strip()
        or values["MYSQL_DATABASE"]
    )
    current_password = values.get("MYSQL_PASSWORD", "")
    password_prompt = "Senha MySQL [pressione Enter para manter a atual]: "
    password = getpass(password_prompt) or current_password

    try:
        server.parse_port(port_raw, "MYSQL_PORT")
    except RuntimeError as error:
        print(f"\n{error}")
        return 1

    test_values = {
        **values,
        "MYSQL_HOST": host,
        "MYSQL_PORT": port_raw,
        "MYSQL_USER": user,
        "MYSQL_PASSWORD": password,
        "MYSQL_DATABASE": database,
        "DB_REQUIRE_MYSQL": "1",
    }

    for key, value in test_values.items():
        os.environ[key] = value
    os.environ["DB_DRIVER"] = "mysql"
    os.environ["DB_REQUIRE_MYSQL"] = "1"

    try:
        server.ensure_schema(force=True)
    except Exception as error:
        print("\nFalha ao conectar ou preparar o banco MySQL:")
        print(error)
        return 1

    test_values["DB_DRIVER"] = "mysql"
    test_values["DB_REQUIRE_MYSQL"] = "1"
    values.update(test_values)
    write_env(values)
    print("\nConexao OK. Banco e tabelas conferidos. Arquivo .env atualizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

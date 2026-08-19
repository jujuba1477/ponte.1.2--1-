# Backend Python + banco de dados

Este projeto usa `server.py` como backend em Python.

## Como configurar

1. Instale Python 3 e marque `Add Python to PATH`.
2. Rode `iniciar-servidor.bat`.
3. Se o MySQL nao estiver instalado ou rodando, o servidor usa automaticamente
   o banco local `ponte_esperanca.sqlite3`.
4. Para usar MySQL de verdade, confirme que o MySQL esta rodando e edite o
   arquivo `.env` com o usuario e a senha reais:

```env
DB_DRIVER=mysql
DB_REQUIRE_MYSQL=1
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_aqui
MYSQL_DATABASE=ponte_esperanca
```

5. Abra:

```text
http://localhost:3000
```

## Modos de banco

- `DB_DRIVER=auto`: tenta MySQL primeiro e usa SQLite local se o MySQL falhar.
- `DB_DRIVER=mysql`: tenta usar MySQL, mas ainda cai para SQLite se `DB_REQUIRE_MYSQL=0`.
- `DB_DRIVER=sqlite`: usa apenas o arquivo SQLite local.
- `DB_REQUIRE_MYSQL=1`: exige MySQL funcionando e mostra erro se nao conectar.

## Rotas da API

- `GET /api/health`
- `POST /api/contact`
- `POST /api/item-donations`
- `POST /api/volunteers`

O banco e as tabelas sao criados automaticamente.

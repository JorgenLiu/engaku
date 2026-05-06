---
name: database
description: Multi-database access via dbhub MCP. Explore schema with search_objects before writing SQL, format DSN strings, prefer read-only exploration.
context: fork
user-invocable: true
disable-model-invocation: false
---

# Database MCP (dbhub)

Multi-database access (PostgreSQL, MySQL, MariaDB, SQL Server, SQLite) through one MCP interface.

## Workflow

1. **Always `search_objects` first** — explore schema before writing SQL.
2. Review columns, types, relationships before querying.
3. Use `execute_sql` only after understanding structure.
4. Prefer read-only exploration (SELECT). For prod, set `readonly = true` in `dbhub.toml` (preferred) or pass `--readonly` at startup.

## Tools

| Tool | Purpose |
|------|---------|
| `search_objects` | Schema exploration — tables, columns, indexes, views |
| `execute_sql` | Run SQL and return results |

## DSN Formats

The `${input:db-dsn}` prompt in `.vscode/mcp.json` expects:

| Database | DSN |
|----------|-----|
| PostgreSQL | `postgres://user:pass@host:5432/db?sslmode=disable` |
| MySQL | `mysql://user:pass@host:3306/db` |
| MariaDB | `mariadb://user:pass@host:3306/db` |
| SQL Server | `sqlserver://user:pass@host:1433/db` |
| SQLite | `sqlite:///absolute/path/to/file.db` or `sqlite://relative/path.db` |

## Environment Variable Alternative

Passwords with `:` / `@` / `#` break URL encoding. Use env vars and leave the DSN empty:

```json
{
  "servers": {
    "dbhub": {
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub@latest", "--transport", "stdio", "--dsn", "${input:db-dsn}"],
      "env": {
        "DB_TYPE": "postgres",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "myuser",
        "DB_PASSWORD": "my@complex#pass",
        "DB_NAME": "mydb"
      }
    }
  }
}
```

## SSL/TLS

- `sslmode=require` for remote servers.
- `sslmode=verify-ca` / `verify-full` with `sslrootcert=/path/to/ca.pem` for RDS / cloud databases.

## SSH Tunneling

For databases behind a bastion:

```json
{
  "command": "npx",
  "args": [
    "@bytebase/dbhub@latest",
    "--dsn", "postgres://user:pass@localhost:5432/db",
    "--ssh-host", "bastion.example.com",
    "--ssh-user", "ubuntu",
    "--ssh-key", "~/.ssh/id_rsa"
  ]
}
```

## Multi-Database Setup

Use distinct `--id` values so tools are named per source:

```json
{
  "servers": {
    "dbhub-prod": {
      "command": "npx",
      "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsnProd}", "--id", "prod"]
    },
    "dbhub-staging": {
      "command": "npx",
      "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsnStaging}", "--id", "staging"]
    }
  }
}
```

Yields `execute_sql_prod` vs `execute_sql_staging`.

## Guardrails

`engaku init` generates `.vscode/dbhub.toml` as the default DBHub config. The DSN comes from `DBHUB_DSN` set in `.vscode/mcp.json` — secrets stay out of the TOML, which is safe to commit.

```toml
[[sources]]
id   = "default"
dsn  = "${DBHUB_DSN}"
lazy = true

[[tools]]
name     = "execute_sql"
source   = "default"
readonly = true
max_rows = 1000
```

- `readonly = true` blocks accidental writes.
- `max_rows` caps result sizes.
- Edit `.vscode/dbhub.toml` to add sources, change guardrails, or enable writes.
- For an inline override without TOML, use `--dsn "${input:db-dsn}"` directly in `.vscode/mcp.json`.
- Always `search_objects` before querying unfamiliar databases.

## Tips

- Start every interaction with `search_objects`.
- `LIMIT` SELECTs to avoid huge result sets.
- Production → `--readonly` unless writes are explicitly required.

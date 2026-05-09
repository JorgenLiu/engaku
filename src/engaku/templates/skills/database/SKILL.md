---
name: database
description: Multi-database access via dbhub MCP. Explore schema with search_objects before writing SQL, format DSN strings, prefer read-only exploration.
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

DSN format by database type (set in `.vscode/dbhub.toml`):

| Database | DSN |
|----------|-----|
| PostgreSQL | `postgres://user:pass@host:5432/db?sslmode=disable` |
| MySQL | `mysql://user:pass@host:3306/db` |
| MariaDB | `mariadb://user:pass@host:3306/db` |
| SQL Server | `sqlserver://user:pass@host:1433/db` |
| SQLite | `sqlite:///absolute/path/to/file.db` or `sqlite://relative/path.db` |

## Environment Variable Interpolation

Use `${VAR_NAME}` in `dbhub.toml` to keep secrets out of the file:

```toml
[[sources]]
id  = "default"
dsn = "${DATABASE_URL}"
```

## SSL/TLS

- `sslmode=require` for remote servers.
- `sslmode=verify-ca` / `verify-full` with `sslrootcert=/path/to/ca.pem` for RDS / cloud databases.

## SSH Tunneling

For databases behind a bastion, configure the tunnel in `dbhub.toml`:

```toml
[[sources]]
id       = "db-via-bastion"
dsn      = "postgres://user:pass@10.0.1.100:5432/mydb"
ssh_host = "bastion.example.com"
ssh_user = "ubuntu"
ssh_key  = "~/.ssh/id_rsa"
```

## Multi-Database Setup

Use multiple `[[sources]]` blocks in `dbhub.toml` — each source ID is appended to tool names:

```toml
[[sources]]
id  = "prod"
dsn = "${DB_PROD_DSN}"

[[sources]]
id  = "staging"
dsn = "${DB_STAGING_DSN}"
```

Yields `execute_sql_prod` and `execute_sql_staging`.

## Guardrails

`engaku init` generates `.vscode/dbhub.toml` as a comment-only stub wired via `--config`. Fill in your own `[[sources]]` and `[[tools]]` entries; see [dbhub.ai/config/toml](https://dbhub.ai/config/toml) for the full schema.

```toml
# [[sources]]
# id   = "default"
# dsn  = "postgres://user:pass@localhost:5432/mydb"
# lazy = true

# [[tools]]
# name     = "execute_sql"
# source   = "default"
# readonly = true      # optional: block writes
```

- Add `readonly = true` to block accidental writes.
- Add `max_rows` to cap result sets.
- Use `${ENV_VAR}` interpolation in the TOML for secrets; the file is safe to commit when env vars hold credentials.
- Always `search_objects` before querying unfamiliar databases.

## Tips

- Start every interaction with `search_objects`.
- `LIMIT` SELECTs to avoid huge result sets.
- Production → `--readonly` unless writes are explicitly required.

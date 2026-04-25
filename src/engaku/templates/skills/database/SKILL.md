---
name: database
description: Multi-database access via dbhub MCP. Explore schema with search_objects before writing SQL, format DSN strings, prefer read-only exploration.
user-invocable: true
disable-model-invocation: false
---

# Database MCP (dbhub)

Use the dbhub MCP server for multi-database access. Supports PostgreSQL, MySQL, MariaDB, SQL Server, and SQLite through a single interface.

## Workflow

1. **Always call `search_objects` first** to explore the schema before writing any SQL.
2. **Understand table structure**: review column names, types, and relationships before querying.
3. **Use `execute_sql`** only after understanding the table structure.
4. **Prefer read-only exploration**: use SELECT queries. For production databases, configure `readonly = true` in `dbhub.toml` (preferred) or pass `--readonly` at startup.

## Tools

| Tool | Purpose |
|------|---------|
| `search_objects` | Explore database schema — tables, columns, indexes, views |
| `execute_sql` | Execute a SQL query and return results |

## DSN Formats

The `${input:db-dsn}` prompt in `.vscode/mcp.json` expects a connection string in one of these formats:

| Database | DSN Format |
|----------|-----------|
| PostgreSQL | `postgres://user:pass@host:5432/db?sslmode=disable` |
| MySQL | `mysql://user:pass@host:3306/db` |
| MariaDB | `mariadb://user:pass@host:3306/db` |
| SQL Server | `sqlserver://user:pass@host:1433/db` |
| SQLite | `sqlite:///absolute/path/to/file.db` or `sqlite://relative/path.db` |

## Environment Variable Alternative

Passwords with special characters (`:`, `@`, `#`) break URL encoding. Use environment variables instead and leave the DSN empty:

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

- Use `sslmode=require` for remote servers.
- Use `sslmode=verify-ca` or `sslmode=verify-full` with `sslrootcert=/path/to/ca.pem` for RDS/cloud databases.

## SSH Tunneling

For databases behind a bastion host, add SSH arguments to the server config:

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

Create multiple server entries in `.vscode/mcp.json` with different `--id` values so tools are named distinctly:

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

This gives you `execute_sql_prod` vs `execute_sql_staging` tools.

## Guardrails

`engaku init` generates `.vscode/dbhub.toml` as the default DBHub configuration. The DSN is passed via the `DBHUB_DSN` environment variable set in `.vscode/mcp.json` — secrets never appear in the TOML file, which is safe to commit.

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

- `readonly = true` prevents accidental writes.
- `max_rows` caps result sizes.
- Edit `.vscode/dbhub.toml` to add more sources, change guardrails, or enable writes.
- For inline `--dsn` without a TOML file (manual override), use `--dsn "${input:db-dsn}"` directly in `.vscode/mcp.json` instead.
- Always inspect schema with `search_objects` before running queries on unfamiliar databases.

## Tips

- Start every database interaction with `search_objects` to understand what tables and columns exist.
- Use `LIMIT` clauses in SELECT queries to avoid returning excessive data.
- For production databases, always use `--readonly` mode unless writes are explicitly needed.

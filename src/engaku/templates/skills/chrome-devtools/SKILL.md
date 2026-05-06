---
name: chrome-devtools
description: Browser automation and DevTools via chrome-devtools-mcp. Screenshot for visual verification, Lighthouse for performance audits, navigate + snapshot for UI automation.
context: fork
user-invocable: true
disable-model-invocation: false
---

# Chrome DevTools MCP

Puppeteer-backed browser control via MCP for automation, visual verification, and performance profiling.

## When to use

- **Visual verification** — screenshot after UI changes.
- **UI automation** — navigate, click, fill, verify.
- **Performance audits** — Lighthouse for Core Web Vitals, accessibility, SEO.
- **JS evaluation** — inspect DOM, console output, client-side logic.
- **Network inspection** — debug API calls, failed fetches, caching headers.

## Tools

| Tool | Purpose |
|------|---------|
| `navigate_page` | Load a URL |
| `take_screenshot` | Capture page as image |
| `click` | Click element by selector |
| `fill` | Type into input |
| `evaluate_script` | Run JS in page context |
| `lighthouse_audit` | Lighthouse report |
| `performance_start_trace` / `performance_stop_trace` | Chrome perf trace |
| `list_network_requests` | Captured network requests |

## Workflow

1. `navigate_page` to target.
2. Interact with `click` / `fill`.
3. `take_screenshot` to verify.
4. `lighthouse_audit` when optimizing load/accessibility.
5. `evaluate_script` for DOM state; `list_network_requests` for API checks.

## Tips

- Headless mode is default in `mcp.json` — keep it for CI / non-interactive use.
- Screenshot before/after for visual diffs.
- Prefer `evaluate_script` over parsing screenshots for structured data.
- Lighthouse audits are slow (~10–30s); only when needed.

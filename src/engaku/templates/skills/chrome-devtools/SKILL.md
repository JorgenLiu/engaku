---
name: chrome-devtools
description: Browser automation and DevTools via chrome-devtools-mcp. Screenshot for visual verification, Lighthouse for performance audits, navigate + snapshot for UI automation.
user-invocable: true
disable-model-invocation: false
---

# Chrome DevTools MCP

Use the chrome-devtools-mcp server for browser automation, visual verification, and performance profiling. The server provides Puppeteer-backed browser control exposed as MCP tools.

## When to use

- **Visual verification**: after making UI changes, take a screenshot to confirm the result matches expectations.
- **UI automation**: navigate to a page, click elements, fill forms, and verify outcomes.
- **Performance audits**: run Lighthouse to get Core Web Vitals, accessibility scores, and SEO checks.
- **JavaScript evaluation**: run arbitrary JS in the page context to inspect DOM state, read console output, or trigger client-side logic.
- **Network inspection**: list network requests to debug API calls, check for failed fetches, or verify caching headers.

## Tools

| Tool | Purpose |
|------|---------|
| `navigate_page` | Load a URL in the browser |
| `take_screenshot` | Capture the current page as an image |
| `click` | Click an element by CSS selector |
| `fill` | Type text into an input field |
| `evaluate_script` | Execute JavaScript in the page context |
| `lighthouse_audit` | Run a Lighthouse audit and return the report |
| `performance_start_trace` | Begin a Chrome performance trace |
| `performance_stop_trace` | Stop the trace and return results |
| `list_network_requests` | List captured network requests |

## Workflow

1. **Navigate** to the target URL with `navigate_page`.
2. **Interact** with the page using `click` and `fill` as needed.
3. **Verify visually** with `take_screenshot` — compare against expectations.
4. **Audit performance** with `lighthouse_audit` when optimizing load times or accessibility.
5. **Debug** with `evaluate_script` to inspect DOM state or `list_network_requests` to check API calls.

## Tips

- Always use `--headless` mode (configured by default in mcp.json) for CI and non-interactive environments.
- Take screenshots before and after changes for visual diff comparison.
- Use `evaluate_script` to extract structured data from the page rather than parsing screenshot images.
- Lighthouse audits can be slow (~10-30s); run them only when performance analysis is specifically needed.

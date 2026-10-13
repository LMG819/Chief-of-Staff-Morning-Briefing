# Composio MCP over HTTP — verified recipe (2026-08-11)

## Context

On 2026-08-11 the Composio MCP server was connected (`hermes mcp list` shows Composio enabled, `hermes mcp test Composio` discovers 7 meta tools), but the `mcp__Composio__*` tools were NOT exposed as callable functions in the session's tool list. Direct `tools/call` on app tools fails:

```
MCP error -32602: Tool COMPOSIO_GET_CURRENT_DATE_TIME not found
```

The working path: StreamableHTTP directly against the MCP endpoint using the cached OAuth token. App tools (GOOGLECALENDAR_*) execute ONLY through COMPOSIO_MULTI_EXECUTE_TOOL.

## Token

`/opt/data/mcp-tokens/Composio.json` → `access_token` (OAuth 2.1 PKCE, ~1-year expiry, `refresh_token` also present). Companion files: `Composio.client.json` (client metadata), `Composio.meta.json` (issuer/endpoints).

## Endpoint + headers

```
POST https://connect.composio.dev/mcp
Content-Type: application/json
Accept: application/json, text/event-stream     # server replies with SSE
Authorization: Bearer <access_token>
Mcp-Session-Id: <from initialize response>      # ALL calls after initialize
```

## Sequence

1. `initialize`:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"hermes-cron","version":"1.0"}}}
```
→ server identifies as "mcp-typescript server on vercel", capabilities `tools.listChanged`. **Capture the `Mcp-Session-Id` response header** — it is required on every subsequent call.

2. `notifications/initialized` (same session id).
3. `tools/call` for meta tools; app tools via `COMPOSIO_MULTI_EXECUTE_TOOL`.

## The 7 meta tools

COMPOSIO_SEARCH_TOOLS, COMPOSIO_GET_TOOL_SCHEMAS, COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH.

## App-tool execution shape (MULTI_EXECUTE)

```json
{"tools":[{"tool_slug":"GOOGLECALENDAR_...","arguments":{...}}],
 "memory":{},"session_id":"<from search data.session.id>","current_step":"..."}
```
- `memory` is REQUIRED — empty object `{}` is accepted.
- `session_id` is the string returned by COMPOSIO_SEARCH_TOOLS at `data.session.id` (verified 2026-08-12; do NOT pass `session:{generate_id:true}` here).
- `sync_response_to_workbench` is required by schema (false keeps it inline).
- Up to 50 logically independent tools per call.

## Response parsing

SSE body: read `data:` lines, JSON-parse each. App results nest inside `result.content[].text` entries as JSON of the shape:
```json
{"data":{"results":[{"response":{"successful":true,"data":{...}},"tool_slug":"...","index":0}],"total_count":1,"success_count":1,"error_count":0}}
```

## Known-good calls

- **GOOGLECALENDAR_GET_CURRENT_DATE_TIME** `{"timezone":"America/New_York"}` → `data.current_datetime` like `"2026-08-11T06:13:44.905630-04:00"` plus `yyyymmdd_datetime`.
- **GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS**
```json
{"time_min":"2026-08-11T00:00:00-04:00","time_max":"2026-08-11T23:59:59-04:00","response_detail":"minimal","single_events":true}
```
→ `summary_view` array with `calendar`, `start`, `end`, `title`, `event_id`, `display_url`. Empty `events[]` + empty `summary_view` = no events in window (check bounds first — inverted/empty windows silently return nothing). Other params available: `q`, `event_types`, `calendar_ids`, `show_deleted`, `max_results_per_calendar`.
- **COMPOSIO_GET_TOOL_SCHEMAS** `{"tool_slugs":["<slug>"]}` → full `input_schema` for any tool, meta or app.

## Calendar quirk observed

The list-all-calendars call queries calendars including "Phases of the Moon" and "Quantum Club" (subscription calendars, noise — skip them). Real events on 2026-08-11 came from the `insibah@mac.com` calendar.

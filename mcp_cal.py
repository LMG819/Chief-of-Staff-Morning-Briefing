#!/usr/bin/env python3
"""Drive Composio MCP (StreamableHTTP) using the cached OAuth token.

Use when Composio MCP tools are not exposed as callable functions in the
session (see references/composio-mcp-http.md). App tools (GOOGLECALENDAR_*)
must run via COMPOSIO_MULTI_EXECUTE_TOOL, never direct tools/call.

Usage:
  python3 mcp_cal.py now [timezone]                 # current datetime (default America/New_York)
  python3 mcp_cal.py events <time_min> <time_max>   # list calendar events in RFC3339 window
"""
import json
import sys
import urllib.request

BASE = "https://connect.composio.dev/mcp"
TOKEN_FILE = "/opt/data/mcp-tokens/Composio.json"


def rpc(payload, session_id=None):
    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + json.load(open(TOKEN_FILE))["access_token"],
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(BASE, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.headers.get("Mcp-Session-Id"), resp.headers.get("Content-Type", ""), resp.read().decode()


def parse_body(body, ctype):
    if "text/event-stream" in ctype or body.lstrip().startswith("event:"):
        for line in body.splitlines():
            if line.startswith("data:"):
                try:
                    return json.loads(line[5:].strip())
                except Exception:
                    continue
        return None
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body[:2000]}


def call_tool(name, args, call_id, sid):
    _, ctype, body = rpc({
        "jsonrpc": "2.0", "id": call_id, "method": "tools/call",
        "params": {"name": name, "arguments": args}
    }, sid)
    res = parse_body(body, ctype)
    if isinstance(res, dict) and "result" in res:
        texts = [c.get("text", "") for c in res["result"].get("content", []) if c.get("type") == "text"]
        return "\n".join(texts)
    return json.dumps(res)[:4000]


def main():
    sid, ctype, body = rpc({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "hermes-cron", "version": "1.0"}
        }
    })
    rpc({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
    if not sid:
        print("NO SESSION:", body[:500])
        sys.exit(1)

    mode = sys.argv[1] if len(sys.argv) > 1 else "now"
    if mode == "now":
        tz = sys.argv[2] if len(sys.argv) > 2 else "America/New_York"
        print(call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", {
            "tools": [{"tool_slug": "GOOGLECALENDAR_GET_CURRENT_DATE_TIME",
                       "arguments": {"timezone": tz}}],
            "memory": {}, "session": {"generate_id": True},
            "current_step": "Get current local date/time"
        }, 2, sid))
    elif mode == "events":
        tmin, tmax = sys.argv[2], sys.argv[3]
        print(call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", {
            "tools": [{"tool_slug": "GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS",
                       "arguments": {
                           "time_min": tmin, "time_max": tmax,
                           "response_detail": "minimal", "single_events": True
                       }}],
            "memory": {}, "session": {"generate_id": True},
            "current_step": "List calendar events in window"
        }, 3, sid))


if __name__ == "__main__":
    main()

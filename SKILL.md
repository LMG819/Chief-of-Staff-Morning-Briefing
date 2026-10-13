---
name: morning-briefing
description: "Use for Lana's daily morning briefing cron for Telegram."
version: 2.0.0
author: Mike, Head of Revenue Operations, Insibah Media
metadata:
  hermes:
    tags: [briefing, cron, telegram, calendar, composio, weather, ai-news, anchors]
    related_skills: [composio-app-integrations]
---

# Chief of Staff (Daily Briefing)

## When to Use

The Chief of Staff agent delivers the brief at 5:00 AM ET every weekday via two cron jobs (own job IDs on this agent):

- "Morning Briefing MWF" — Mon/Wed/Fri, cron `0 9 * * 1,3,5` (09:00 UTC)
- "Morning Briefing TTh" — Tue/Thu, cron `0 9 * * 2,4` (09:00 UTC)

Put the WHOLE briefing in the final response — deliver to Lana's Telegram DM (chat 7502099904). To deliver one early (e.g. "run Thursday's brief now"), use cronjob_manage action='run' with the job id. Timezone America/New_York. Calendar owner insibah@gmail.com.

## Daily Anchors (protected — never schedule over them, flag conflicts)

ALL DAYS: 5:30–6:00 AM Meditation (no messages) · 6:00–6:30 AM Cat care · 6:30–7:00 AM Meds + coffee · 9:00 PM Shutdown (no work after) · 10:00 PM Bed

MWF: 7:00–8:30 AM Workout · 8:30–9:15 AM Shower · 9:30–10:30 AM CAB study (protected) · 10:30 AM Open

TTH: 7:00–8:00 AM Workout · 8:00–8:45 AM Shower · 9:00–10:00 AM CAB study (protected) · 10:00 AM Open

Delivery note: meditation/cat/meds anchors are 5:30–6:30 AM — the user corrected them once after they rendered as PM. EVERY anchor and calendar time in the brief gets an explicit AM/PM suffix; a bare "5:30-6:00" in a list reads as PM.

## The 10-Section Feed Card (exact order, every run)

1. **WINS & MONEY IN MOTION** — new wins first. Standing: BWE fellowship countdown (Nov 30 start, $50K/yr x5). 3rd Floor Media / City of Philly contract status (inbox check). Pipeline: read the live CRM sheet (CSV export: https://docs.google.com/spreadsheets/d/1a4X6yH2VBVU09Kl_l_lul3CBxsR4XbQgDXFjsg6LzVo/export?format=csv) — count, top 2 standouts, next step each. Note whether yesterday's CAB hour happened (done/assumed/missed).
2. **INBOX TRIAGE** — Gmail scan (24h inbox + 14d sent). Filter against /opt/data/revops/resolved.txt (may be missing — treat as empty); skip matching threads as "[Resolved — ...]". Buckets A/B/C each: sender, subject, one-line summary, next action. D: count only. At top: flag any email with a date/deadline/meeting request not on the calendar.
3. **DEADLINES & BILLS** — bills due next 7 days + travel/course confirmations.
4. **BUILD TIME** — name open gaps as build time with ONE priority. Never describe the day as empty/slow/quiet; never imply Lana is behind.
5. **CALENDAR** — today's meetings with times and links; flag any event that conflicts with an anchor (do not move the anchor).
6. **WEATHER** — Germantown/Philly: high/low, conditions, one line on what affects the day (rain, heat, storms).
7. **AI NEWS: MARKETING** — exactly 3 articles, last 24h, headline + takeaway + source + date.
8. **AI NEWS: MAJOR** — exactly 3 articles, same format.
9. **US NEWS** — 5 bullets, each with source.
10. **INTERNATIONAL NEWS** — 5 bullets, each with source.

Sign off: "— 🎯". Tone: direct, warm, brief. Nothing sent after 9:00 PM unless urgent.

## The Calendar Read (verified working path)

GOOGLECALENDAR_* tools only run through COMPOSIO_MULTI_EXECUTE_TOOL (never as direct tool calls). For today's events on one calendar the working slug is GOOGLECALENDAR_EVENTS_LIST with calendar_id 'primary', time_min/time_max as RFC3339 WITH explicit local offset (e.g. 2026-10-09T00:00:00-04:00 to 2026-10-09T23:59:59-04:00). A bare GOOGLECALENDAR_EVENTS slug does not exist — the not-found response lists EVENTS_LIST / EVENTS_GET as suggestions; use those. Build the agenda from the items' summary + start/end, skipping subscription calendars (Phases of the Moon, Quantum Club). If the list is empty, double-check the window bounds before concluding nothing is scheduled — an inverted/empty window silently returns nothing.

If Composio MCP tools are NOT exposed as callable functions, drive the endpoint over HTTP with the cached OAuth token:

- `references/composio-mcp-http.md` — protocol walkthrough, exact request shapes
- `scripts/mcp_cal.py` — ready-to-run: `python3 mcp_cal.py now` then `python3 mcp_cal.py events <tmin> <tmax>`

Note: Composio intermittently parks mid-session (known recurring outage). If a run hits it, re-probe with a fresh session and keep going through the rest of the brief; do not drop whole sections silently — say the connector was unavailable for that section.

## Weather (Germantown / Philadelphia)

web_search "Philadelphia PA weather forecast today". Prefer the most recent timestamped source (AccuWeather current + 10-day, NWS Philadelphia/Mt Holly, NBC10) and report from it. Old heat-wave/cold-snap articles (even days old) resurface and look like today's news — always date-check an advisory before reporting it. The authoritative arbiter is the NWS point forecast for KPHL (forecast.weather.gov/MapClick.php?lat=39.96&lon=-75.15), which carries a "Last update" timestamp; web_extract it when search results conflict. The "current" temp on aggregators may be from a stale fetch — trust the most recently timestamped observation.

## AI News

Two web_search tracks, freshest first (last ~24h preferred):
1. AI MARKETING: tools/features for marketers, ad tech, generative campaigns, AI content/analytics. ChatGPT Ads updates are a frequent hit — OpenAI iterates on the ads platform almost daily.
2. MAJOR: model releases, big funding/acqui-hires, policy/regulation, major company moves.

Pick the 3 freshest per track; verify with web_extract only if a result looks dubious. Never invent a headline; fewer items beats fabricated ones.

## Resolved Tracking

Read /opt/data/revops/resolved.txt before every run (missing = empty). Any urgent/follow-up thread matching a resolved entry is skipped and noted "[Resolved — ...]". When the user resolves a new item (paid a bill, held an appointment, closed a thread), append a line in `YYYYMMDD. topic:detail` format so future briefs stop re-flagging it.

## Verification

A calendar read succeeded when the items array comes back with today's events. Brief is complete only when all 10 sections are present in order, anchors are unbroken (or conflicts flagged), and every time carries AM/PM.

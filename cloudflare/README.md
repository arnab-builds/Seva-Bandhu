# Seva Bandhu Health Monitor Cloudflare Worker

A lightweight Cloudflare Worker triggered every 10 minutes (`*/10 * * * *`) by Cloudflare Cron to monitor application and database health.

## Architecture

```text
Cloudflare Cron (`*/10 * * * *`)
      ↓
Cloudflare Worker (sevabandhu-health-monitor)
      ↓
 ┌───────────────────────────────────────┐
 │                                       │
 ▼                                       ▼
Render Django (/health/db/)          Supabase API/health
 │                                   (if configured)
 ▼
Supabase PostgreSQL (SELECT 1)
```

## Security Design

- **Zero Database Credentials**: The Worker never receives or uses `DATABASE_URL`, PostgreSQL usernames, passwords, or direct DB connections.
- **Zero Secrets**: No Django secret keys, Cloudinary URLs, or Supabase service-role keys are exposed or configured.
- **Primary Database Check**: The primary health check goes through Render (`GET /health/db/`), where Django executes a safe `SELECT 1` query against the Supabase PostgreSQL database.
- **Secondary Supabase Check**: If configured (`SUPABASE_HEALTH_URL`), the Worker probes the Supabase REST/Auth API. If not configured, the Worker reports `NOT_CONFIGURED` without falsifying results.
- **Zero Credential Logging**: Authorization headers and anon keys are never output to logs.

## Files

- `wrangler.jsonc`: Wrangler configuration defining Worker name, entrypoint, 10-minute cron trigger, and environment variables.
- `src/index.js`: Worker implementation handling both scheduled cron events and on-demand HTTP requests.
- `package.json`: Worker project metadata and test runner scripts.
- `test/test_monitor.js`: Unit tests verifying health status evaluation and fault tolerance across all error scenarios.

## Environment Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `HEALTHCHECK_URL` | Render Django DB health endpoint | `https://seva-bandhu-41dh.onrender.com/health/db/` |
| `SUPABASE_HEALTH_URL` | *(Optional)* Independent Supabase REST/Auth endpoint | `https://<project-ref>.supabase.co/rest/v1/` |
| `SUPABASE_ANON_KEY` | *(Optional)* Supabase public anon key | `ey...` |

## Local Testing

```bash
cd cloudflare
npm test
```


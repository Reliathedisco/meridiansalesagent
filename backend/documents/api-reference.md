# Meridian Analytics — API Reference

The Meridian REST API lets you ingest events, query analytics, and manage your workspace programmatically. The API is available on the Growth and Enterprise plans.

## Authentication

All API requests require an API key passed via the `Authorization` header:

```
Authorization: Bearer mk_live_your_api_key_here
```

Generate API keys in **Settings → Developer → API Keys**. Keys are scoped to a workspace and can be restricted to read-only or read-write.

- **Live keys** (`mk_live_`) are for production use.
- **Test keys** (`mk_test_`) are for development — events sent with test keys are stored separately and don't affect your production data.

## Base URL

All API endpoints use the following base URL:

```
https://api.meridian.io/v1
```

## Rate Limits

- **Growth plan**: 500 requests/minute per API key.
- **Enterprise plan**: Unlimited (fair use policy applies).
- Rate-limited responses return HTTP 429 with a `Retry-After` header.

## Event Ingestion

### POST /events

Send one or more events to Meridian.

**Request body:**
```json
{
  "events": [
    {
      "event": "page_view",
      "user_id": "usr_123",
      "properties": {
        "page": "/pricing",
        "referrer": "google.com"
      },
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Response (202 Accepted):**
```json
{
  "accepted": 1,
  "failed": 0
}
```

- Maximum batch size: 1000 events per request.
- Events older than 30 days are rejected on Starter; 12 months on Growth.
- If `timestamp` is omitted, the server uses the current time.

### POST /events/identify

Associate user properties with a user ID for segmentation.

```json
{
  "user_id": "usr_123",
  "traits": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "plan": "growth",
    "company": "Acme Inc"
  }
}
```

## Query API

### POST /query

Run an MQL (Meridian Query Language) query against your event data.

```json
{
  "query": "SELECT count() FROM events WHERE event = 'signup' AND timestamp > now() - interval 7 day GROUP BY date(timestamp)",
  "format": "json"
}
```

**Response:**
```json
{
  "columns": ["date", "count"],
  "rows": [
    ["2025-01-09", 142],
    ["2025-01-10", 158],
    ["2025-01-11", 131]
  ],
  "query_time_ms": 23
}
```

Supported formats: `json`, `csv`, `parquet`.

### GET /funnels/:id

Retrieve a funnel analysis by its dashboard ID.

### GET /cohorts/:id

Retrieve a cohort analysis by its dashboard ID.

## SDK Installation

### JavaScript / TypeScript

```bash
npm install @meridian/sdk
```

```javascript
import { Meridian } from '@meridian/sdk';

const meridian = new Meridian({ apiKey: 'mk_live_...' });

meridian.track('button_click', {
  button_id: 'cta-signup',
  page: '/landing'
});
```

### Python

```bash
pip install meridian-analytics
```

```python
from meridian import Meridian

client = Meridian(api_key="mk_live_...")
client.track("button_click", user_id="usr_123", properties={"page": "/landing"})
```

### Go

```bash
go get github.com/meridian-analytics/meridian-go
```

## Webhooks

Configure webhooks in **Settings → Developer → Webhooks** to receive real-time notifications when:

- An anomaly is detected
- A funnel conversion rate drops below a threshold
- A new user segment is identified

Webhook payloads are signed with HMAC-SHA256. Verify the `X-Meridian-Signature` header to ensure authenticity.

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Bad Request — malformed JSON or invalid parameters |
| 401 | Unauthorized — missing or invalid API key |
| 403 | Forbidden — API key lacks required permissions |
| 404 | Not Found — resource doesn't exist |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error — contact support if persistent |

## Pagination

List endpoints support cursor-based pagination:

```
GET /events?cursor=eyJpZCI6MTIzfQ&limit=100
```

The response includes a `next_cursor` field. Pass it as the `cursor` parameter to fetch the next page. When `next_cursor` is null, there are no more results.

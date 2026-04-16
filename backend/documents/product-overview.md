# Meridian Analytics — Product Overview

Meridian Analytics is a B2B data intelligence platform built for engineering and product teams. It provides real-time application monitoring, advanced analytics, and AI-powered insights — all accessible through a modern dashboard or a fully-featured REST API.

## Core Features

Meridian offers a comprehensive suite of analytics tools:

- **Event Tracking**: Ingest and query billions of custom events with sub-second latency. Events are schemaless — send any JSON payload and Meridian auto-indexes it for fast querying.
- **Funnel Analysis**: Build multi-step conversion funnels with automatic drop-off detection. Supports time-bounded funnels (e.g., "completed checkout within 30 minutes of adding to cart").
- **Cohort Segmentation**: Group users by behavior, demographics, or custom properties. Compare cohort retention, engagement, and revenue over time.
- **Real-Time Dashboards**: Create drag-and-drop dashboards with live-updating charts. Supports line, bar, area, pie, heatmap, and table visualizations.
- **AI Anomaly Detection**: Meridian's ML pipeline continuously monitors metrics and alerts on unusual patterns — traffic spikes, conversion drops, error rate increases — before they impact users.

## Integrations

Meridian integrates with the tools your team already uses:

- **Data Warehouses**: BigQuery, Snowflake, Redshift — bidirectional sync for enrichment and export.
- **Messaging**: Slack, Microsoft Teams, PagerDuty — real-time alerts delivered where your team works.
- **Developer Tools**: GitHub, Jira, Linear — link analytics events to engineering workflows.
- **CDPs**: Segment, mParticle, RudderStack — import user traits and events seamlessly.

## Architecture

Meridian runs on a distributed, event-driven architecture designed for scale:

- **Ingest layer**: HTTP + WebSocket endpoints that accept events at up to 100K events/second per workspace.
- **Processing layer**: Stream processing via Apache Kafka for real-time aggregation and anomaly detection.
- **Storage layer**: ClickHouse for fast analytical queries, S3 for long-term raw event storage.
- **Query engine**: Custom SQL-like query language (MQL) that compiles to optimized ClickHouse queries.

## Use Cases

Teams use Meridian for a wide range of analytics needs:

- **Product teams**: Track feature adoption, measure A/B test results, understand user journeys.
- **Engineering teams**: Monitor application health, track error rates, correlate deploys with metric changes.
- **Growth teams**: Build and optimize conversion funnels, run retention analysis, segment users for campaigns.
- **Executive teams**: Real-time KPI dashboards, automated weekly reports, board-ready visualizations.

## Platform Support

Meridian provides first-party SDKs for all major platforms:

- **Web**: JavaScript/TypeScript SDK with automatic page view and click tracking.
- **Mobile**: iOS (Swift) and Android (Kotlin) SDKs with offline event buffering.
- **Backend**: Node.js, Python, Ruby, Go, and Java SDKs for server-side event tracking.
- **API**: Full REST API for custom integrations. See the API Reference for details.

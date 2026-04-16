# Meridian Analytics — Onboarding Guide

Welcome to Meridian Analytics. This guide walks you through setting up your workspace, sending your first events, building dashboards, and inviting your team.

## Step 1: Create Your Workspace

1. Sign up at https://app.meridian.io/signup.
2. Choose a workspace name (e.g., your company name). This can be changed later.
3. Select your data residency region: US (N. Virginia) or EU (Ireland).
4. You'll land on an empty dashboard — that's normal! Let's get data flowing.

## Step 2: Install the SDK

Choose the SDK for your platform. The JavaScript SDK is the most common starting point.

**JavaScript (npm):**
```bash
npm install @meridian/sdk
```

**JavaScript (CDN):**
```html
<script src="https://cdn.meridian.io/sdk/v2/meridian.min.js"></script>
```

**Python:**
```bash
pip install meridian-analytics
```

After installation, initialize the SDK with your API key (found in Settings → Developer → API Keys):

```javascript
import { Meridian } from '@meridian/sdk';
const meridian = new Meridian({ apiKey: 'mk_live_...' });
```

## Step 3: Send Your First Event

Track a simple event to verify your integration:

```javascript
meridian.track('test_event', { source: 'onboarding' });
```

Head to the **Live Events** tab in your dashboard. You should see the event appear within a few seconds. If not, check your API key and network connectivity.

## Step 4: Set Up User Identification

To unlock cohort analysis and user-level insights, identify your users:

```javascript
meridian.identify('usr_123', {
  name: 'Jane Doe',
  email: 'jane@example.com',
  plan: 'growth',
  signed_up: '2025-01-10'
});
```

Call `identify` when a user logs in or when their profile changes. All subsequent `track` calls will be associated with this user.

## Step 5: Build Your First Dashboard

1. Go to **Dashboards → Create New**.
2. Click **Add Widget** and choose a visualization type (line chart is a good start).
3. Select your event (e.g., `test_event`) and a metric (count, unique users, etc.).
4. Set a time range and click **Save**.

Tips for effective dashboards:
- Group related metrics together (e.g., "Signup Funnel", "Feature Adoption").
- Use the **auto-refresh** toggle for real-time monitoring.
- Pin important dashboards to the sidebar for quick access.

## Step 6: Create a Conversion Funnel

Funnels help you understand where users drop off in multi-step flows.

1. Go to **Funnels → Create New**.
2. Add steps in order (e.g., `page_view` → `signup_started` → `signup_completed`).
3. Set a conversion window (e.g., 30 minutes between steps).
4. Click **Analyze** to see conversion rates and drop-off points.

## Step 7: Set Up Alerts

Don't wait to discover problems — let Meridian notify you automatically.

1. Go to **Alerts → Create New**.
2. Choose a metric (e.g., error rate, conversion rate, event volume).
3. Set a threshold or enable **AI anomaly detection** (Growth and Enterprise plans).
4. Choose notification channels: email, Slack, Teams, or PagerDuty.

## Step 8: Invite Your Team

1. Go to **Settings → Team → Invite Members**.
2. Enter email addresses and assign roles:
   - **Admin**: Full access including billing and API keys.
   - **Member**: Can create and edit dashboards, view all data.
   - **Viewer**: Read-only access to dashboards.
3. Members receive an email invitation and can join immediately.

## Common Issues

**Events not appearing in the dashboard?**
- Verify your API key is correct and active.
- Check that you're using a live key (`mk_live_`), not a test key (`mk_test_`).
- Ensure your clock isn't significantly skewed — events with timestamps more than 5 minutes in the future are rejected.

**SDK throwing errors?**
- Make sure you're on the latest SDK version: `npm update @meridian/sdk`.
- Check the browser console or server logs for specific error messages.
- If behind a corporate proxy, whitelist `*.meridian.io` and `*.meridian-cdn.io`.

**Need help?**
- Documentation: https://docs.meridian.io
- Email: support@meridian.io
- Community Slack: https://meridian.io/slack
- Enterprise customers: Contact your dedicated account manager.

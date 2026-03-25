# Instagram Integration Plugin -- Setup Guide

## Step 1: Register as a Meta Developer

If you haven't registered as a Meta developer, do this first — otherwise the "Create App" button won't appear.

1. Go to [developers.facebook.com](https://developers.facebook.com/) and click **"Get Started"**
2. Accept Platform Terms and Developer Policies
3. Verify your **phone number** and **email address**

> **Can't see "Create App"?** You may have hit the 15-app limit, need to clear your browser cache, or can try the direct URL: [developers.facebook.com/apps/creation/](https://developers.facebook.com/apps/creation/)

## Step 2: Create or Reuse a Meta App

> **Already have a Meta App?** If you already have an app for the Facebook Pages or Threads plugin, you don't need to create a new one. Facebook, Instagram, and Threads all use Meta's Graph API and can share a single app. Just go to your existing app's dashboard, add **"Instagram Graph API"** as a product, and skip to Step 3.

Meta now uses a **use-case-based flow** instead of the older "app type" selection.

1. Go to [developers.facebook.com/apps/creation/](https://developers.facebook.com/apps/creation/)
2. Enter an **app name** (e.g., "My Page Manager") and **contact email**, click **Next**
   > **Important:** Do not include Meta brand terms (FB, Face, Book, Insta, Gram, Rift) in your app name — Meta will reject it.
3. Select the use case: **"Manage everything on your Page"** — this enables the Instagram Graph API
4. Optionally add compatible use cases (e.g., "Access Threads API" if you also use the Threads plugin)
5. **Business Portfolio:** Select "I don't want to connect a business portfolio yet" for development/testing
6. Click **"Go to dashboard"**
7. In your app dashboard, find **"Instagram Graph API"** under Products and ensure it's added

> **Note:** Older guides reference selecting "Business" as the app type — Meta replaced this with the use-case flow.

## Step 3: Connect Your Instagram Account

Your Instagram account must be:
- A **Business** or **Creator** account (not Personal)
- **Linked to a Facebook Page**

To convert to Business:
1. Open Instagram > Settings > Account > Switch to Professional Account
2. Choose Business or Creator
3. Connect to a Facebook Page

## Step 4: Generate Access Token

### Option A: Graph API Explorer (Quick Start)
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click "Generate Access Token"
4. Select permissions: `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`, `instagram_manage_insights`
5. Click "Generate Access Token" and authorize

### Option B: Facebook Login Flow (Production)
Implement the full OAuth flow for production use.

## Step 5: Exchange for Long-Lived Token

Short-lived tokens expire in ~1 hour. Exchange for a long-lived token (60 days):

```bash
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

## Step 6: Get Your Instagram User ID

```bash
curl -s "https://graph.instagram.com/v21.0/me?fields=id,username&access_token=YOUR_TOKEN"
```

The `id` field in the response is your Instagram User ID.

## Step 7: Configure the Plugin

1. Open Agent Zero WebUI
2. Go to Settings > External Services > Instagram Integration
3. Enter your **long-lived access token** in the Access Token field
4. Enter your **Instagram User ID** (numeric) in the User ID field
5. Click "Save Instagram Settings"
6. Click "Test Connection" to verify

## Token Refresh

Long-lived tokens are valid for 60 days. The plugin does not auto-refresh tokens (the API requires the original token to be valid). Before expiry, refresh manually:

```bash
curl -s "https://graph.instagram.com/refresh_access_token?\
grant_type=ig_refresh_token&\
access_token=YOUR_CURRENT_TOKEN"
```

## Required Permissions

| Permission | Purpose |
|-----------|---------|
| `instagram_basic` | Read profile, media feed, stories |
| `instagram_content_publish` | Post photos, carousels, reels |
| `instagram_manage_comments` | Read, post, reply, delete comments |
| `instagram_manage_insights` | Access account and media analytics |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No access token configured" | Enter token in plugin settings |
| "No Instagram User ID configured" | Enter numeric user ID in settings |
| "Access token expired" | Generate and exchange a new token |
| "Permission denied" | Ensure all 4 permissions are granted |
| Photo publish fails | Image URL must be publicly accessible (not localhost) |
| Rate limit errors | Wait for the current hour to reset (200 calls/hour) |

# Instagram Integration Plugin Documentation

## Overview

Post photos, carousels, reels, and manage Instagram content via Meta's Instagram Graph API. Requires an Instagram Business or Creator account linked to a Facebook Page.

## Contents

- [Quick Start](QUICKSTART.md) -- Installation and first-use guide
- [Setup](SETUP.md) -- Detailed credential setup instructions
- [Development](DEVELOPMENT.md) -- Contributing and development setup

## Architecture

```
Agent Zero <-> Tool Layer <-> Instagram Client <-> Instagram Graph API (v21.0)
                              (async aiohttp)      (REST + access_token auth)
```

### 2-Step Publishing Flow
1. **Create Container**: POST `/{ig-user-id}/media` with image/video URL + caption
2. **Publish Container**: POST `/{ig-user-id}/media_publish` with container ID

### Key Design Decisions
- **aiohttp** for async HTTP (consistent with other A0 plugins)
- **Rate limiter** with 200 calls/hour tracking and safety buffer
- **Sanitization layer** with NFKC normalization and prompt injection defense
- **Atomic file writes** (0o600 permissions) for tokens and usage data

## Tools

| Tool | Description |
|------|-------------|
| `instagram_post` | Post photos, carousels, and reels (2-step publish) |
| `instagram_read` | Read media feed, specific posts, stories |
| `instagram_comment` | List, post, reply to, delete comments |
| `instagram_search` | Hashtag search and content discovery |
| `instagram_manage` | Delete media (API-published only) |
| `instagram_insights` | Account and media analytics |
| `instagram_profile` | View profile information |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plugins/instagram/instagram_test` | POST | Test connection, return user info + usage stats |
| `/api/plugins/instagram/instagram_config_api` | GET/POST | Read/write plugin config (token masking) |

## Rate Limits

- 200 API calls per user per hour (Instagram Graph API limit)
- Plugin tracks usage per hour and provides warnings when approaching limits
- Rate limiter in the client has a 10-call safety buffer

## Known Behaviors

- **Duplicate posts/comments on retry:** If Agent Zero's LLM encounters an error after a tool call completes, its retry mechanism may re-execute the same tool call, resulting in duplicate posts, comments, or replies. This is an A0 framework behavior, not a plugin bug. Check your Instagram account and manually delete any duplicates if this occurs.
- **Hashtag search requires App Review:** Hashtag search (recent/top media) requires Facebook's "Public Content Access" feature, which must be approved via App Review. In Development mode, hashtag search will fail with a permission error.
- **Business Discovery limitations:** Username-based profile lookups (`@handle`) only work for Business/Creator accounts. Personal accounts cannot be found via the API.
- **Stories not publishable:** The Instagram Graph API does not support creating Stories. Only feed posts, carousels, and reels can be published.
- **Media deletion not supported:** The Instagram Graph API does not support deleting posts (neither organic nor API-published). Posts must be deleted manually through the Instagram app.
- **Image URL requirement:** Instagram's API fetches images server-side from a public URL. Local files and authenticated URLs (e.g., social media post URLs) cannot be used directly.

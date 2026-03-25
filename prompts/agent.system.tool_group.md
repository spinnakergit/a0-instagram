## Instagram Integration

Tools for posting, reading, searching, and managing content on Instagram via Meta's Instagram Graph API.

### Available Tools

**Publishing**: `instagram_post` (photos, carousels, reels)
**Reading**: `instagram_read`, `instagram_search`, `instagram_insights`
**Engaging**: `instagram_comment`
**Managing**: `instagram_manage`, `instagram_profile`

### Key Concepts

- **Instagram Graph API**: REST API for Business/Creator accounts linked to Facebook Pages
- **Media ID**: Numeric identifier for posts (e.g., `17895695668004550`)
- **2-Step Publishing**: Create a media container, then publish it (required for all post types)
- **Caption limit**: 2,200 characters per post, max 30 hashtags
- **Rate limit**: 200 API calls per user per hour
- **Business/Creator only**: Personal accounts are not supported by the Graph API

### Authentication

Uses a long-lived access token from Facebook Login. Requires:
- A Facebook App with Instagram Graph API product
- Instagram Business or Creator account linked to a Facebook Page
- Permissions: instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_insights

### Best Practices

- Images must be publicly accessible URLs (the API fetches them server-side)
- Video uploads (reels) may take time to process — the tool polls automatically
- Carousels require 2-10 items
- Use `instagram_read` with action "feed" to find media IDs for comments/insights
- Hashtag search is limited to 30 unique hashtags per 7-day rolling window

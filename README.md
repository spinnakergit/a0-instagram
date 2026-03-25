# Instagram Integration Plugin for Agent Zero

Post photos, carousels, reels, and manage Instagram content via Meta's Instagram Graph API.

## Quick Start

1. Copy the plugin to your Agent Zero instance:
   ```bash
   ./install.sh
   ```
2. Configure your access token and user ID in the WebUI (Settings > External Services > Instagram Integration)
3. Restart Agent Zero

## Features

- **Publish** photos, carousels (2-10 images), and reels via 2-step publishing flow
- **Read** media feed, individual posts, and active stories
- **Comment** management: list, post, reply, delete
- **Search** content by hashtag (recent and top)
- **Insights** for account performance and individual media analytics
- **Profile** viewing for authenticated user and lookups
- **Media management**: delete API-published posts
- **Security**: prompt injection defense, NFKC normalization, atomic file writes
- **Rate limiting**: 200 API calls/hour tracking with safety buffer

## Tools

| Tool | Description |
|------|-------------|
| `instagram_post` | Publish photos, carousels, and reels |
| `instagram_read` | Read media feed, individual posts, and stories |
| `instagram_comment` | List, post, reply to, and delete comments |
| `instagram_search` | Search content by hashtag (recent and top) |
| `instagram_manage` | Media management operations |
| `instagram_insights` | Account and media analytics |
| `instagram_profile` | View profile and look up users by username |

## Required Permissions

- `instagram_basic` — Read profile info, media, and account data
- `instagram_content_publish` — Publish photos, carousels, and reels
- `instagram_manage_comments` — Read and manage comments
- `instagram_manage_insights` — Access account and media analytics

## Requirements

- Instagram Business or Creator account (linked to a Facebook Page)
- Facebook App with Instagram Graph API product
- Long-lived access token with the permissions listed above

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Setup Guide](docs/SETUP.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Full Documentation](docs/README.md)

## Testing

```bash
# Automated regression (requires running container)
bash tests/regression_test.sh <container> <port>

# Human verification
# Follow tests/HUMAN_TEST_PLAN.md
```

## License

MIT -- see [LICENSE](LICENSE)

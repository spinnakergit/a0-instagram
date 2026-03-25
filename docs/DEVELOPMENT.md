# Instagram Integration Plugin -- Development Guide

## Project Structure

```
a0-instagram/
├── plugin.yaml           # Plugin manifest
├── default_config.yaml   # Default settings
├── initialize.py         # Dependency installer (aiohttp, requests)
├── install.sh            # Deployment script
├── .gitignore            # Git ignore rules
├── helpers/
│   ├── __init__.py
│   ├── instagram_auth.py # Token management, usage tracking
│   ├── instagram_client.py # Async aiohttp client (2-step publishing)
│   └── sanitize.py       # Content validation, injection defense, formatting
├── tools/
│   ├── instagram_post.py      # Post photos, carousels, reels
│   ├── instagram_read.py      # Read feed, posts, stories
│   ├── instagram_comment.py   # Comment management
│   ├── instagram_search.py    # Hashtag search
│   ├── instagram_manage.py    # Delete media
│   ├── instagram_insights.py  # Account and media insights
│   └── instagram_profile.py   # Profile info
├── prompts/
│   ├── agent.system.tool_group.md
│   └── agent.system.tool.instagram_*.md (7 files)
├── api/
│   ├── instagram_test.py        # Connection test endpoint
│   └── instagram_config_api.py  # Config read/write endpoint
├── webui/
│   ├── main.html    # Dashboard (status, stats, test button)
│   └── config.html  # Settings (access_token, ig_user_id)
├── skills/
│   ├── instagram-post/SKILL.md
│   ├── instagram-research/SKILL.md
│   └── instagram-engage/SKILL.md
├── tests/
│   ├── regression_test.sh    # Automated test suite (~35 tests)
│   └── HUMAN_TEST_PLAN.md    # Manual verification plan (46 tests)
└── docs/
    ├── README.md
    ├── QUICKSTART.md
    ├── SETUP.md
    └── DEVELOPMENT.md
```

## Development Setup

1. Start the dev container:
   ```bash
   docker start agent-zero-dev
   ```

2. Install the plugin:
   ```bash
   docker cp a0-instagram/. agent-zero-dev:/a0/usr/plugins/instagram/
   docker exec agent-zero-dev ln -sf /a0/usr/plugins/instagram /a0/plugins/instagram
   docker exec agent-zero-dev touch /a0/usr/plugins/instagram/.toggle-1
   docker exec agent-zero-dev supervisorctl restart run_ui
   ```

3. Run tests:
   ```bash
   bash tests/regression_test.sh agent-zero-dev 50083
   ```

## Adding a New Tool

1. Create `tools/instagram_<action>.py` with a Tool subclass
2. Create `prompts/agent.system.tool.instagram_<action>.md`
3. Add tests in `tests/regression_test.sh`
4. Update `prompts/agent.system.tool_group.md`
5. Update documentation

## Code Patterns

- **Tool base class**: `from helpers.tool import Tool, Response`
- **Config access**: `plugins.get_plugin_config("instagram", agent=self.agent)`
- **API handlers**: `requires_csrf() -> True` (never False)
- **WebUI attributes**: `data-ig=` prefix (never bare IDs)
- **WebUI fetch**: `globalThis.fetchApi || fetch`
- **Logging**: Use `logging.getLogger()`, never `print()`
- **File writes**: Atomic with `os.replace()` and `0o600` permissions
- **Client lifecycle**: Always `await client.close()` in `try/finally`
- **Tool returns**: `Response(message=..., break_loop=False)`

## Thumbnail

The plugin thumbnail is stored in the plugin index repo (not this repo) at `plugins/instagram/thumbnail.png`.

| Field | Value |
|-------|-------|
| **Dimensions** | 256x256 px (square) |
| **Format** | Indexed PNG (palette mode) |
| **Max file size** | 20 KB |
| **Design** | White Instagram camera glyph on gradient background (purple #833AB4 -> pink #E1306C -> orange #F77737 -> yellow #FCAF45) with rounded corners |

A pre-generated thumbnail is available at `_standards/thumbnails/instagram.png` and is included in the index PR during publishing. If no custom thumbnail is provided, the upstream auto-generates a fallback via AI image generation.

To regenerate:
```bash
python3 _standards/scripts/generate_thumbnail.py instagram "IG" "#E4405F"
```

See `_standards/THUMBNAIL_STANDARD.md` for full requirements and design guidelines.

## Instagram Graph API Reference

- Base URL: `https://graph.instagram.com/v21.0`
- Auth: Long-lived access token as query parameter
- Rate limit: 200 calls/user/hour
- Publishing: 2-step (create container, then publish)
- Media types: IMAGE, VIDEO, CAROUSEL_ALBUM, REELS
- [Official docs](https://developers.facebook.com/docs/instagram-api)

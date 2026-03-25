"""API endpoint: Test Instagram Graph API connection.
URL: POST /api/plugins/instagram/instagram_test
"""
from helpers.api import ApiHandler, Request, Response


class InstagramTest(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            from plugins.instagram.helpers.instagram_auth import get_instagram_config, is_authenticated, get_usage

            config = get_instagram_config()
            token = config.get("access_token", "")
            ig_user_id = config.get("ig_user_id", "")

            if not token:
                return {"ok": False, "error": "No access token configured"}
            if not ig_user_id:
                return {"ok": False, "error": "No Instagram User ID configured"}

            authenticated, info = is_authenticated(config)
            if not authenticated:
                return {"ok": False, "error": info}

            usage = get_usage(config)
            return {
                "ok": True,
                "user": info,
                "usage": {
                    "api_calls": usage.get("api_calls", 0),
                    "posts_published": usage.get("posts_published", 0),
                    "hour": usage.get("hour", ""),
                },
            }
        except Exception as e:
            return {"ok": False, "error": f"Connection failed: {type(e).__name__}: {e}"}

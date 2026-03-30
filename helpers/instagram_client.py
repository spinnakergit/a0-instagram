"""
Instagram Graph API async client with rate limiting and retry logic.

All Instagram Graph API calls use HTTPS REST endpoints.
Publishing follows a 2-step process: create media container, then publish it.

Base URL: https://graph.instagram.com/v21.0
Rate limit: 200 API calls per user per hour.
"""

import asyncio
import time
import json
import logging
import aiohttp

logger = logging.getLogger("instagram_client")

BASE_URL = "https://graph.facebook.com/v21.0"


class InstagramRateLimiter:
    """Track rate limits from API response headers."""

    def __init__(self):
        self._call_count = 0
        self._hour_start = time.time()
        self._lock = asyncio.Lock()

    async def wait(self):
        """Block if approaching the 200 calls/hour limit."""
        async with self._lock:
            now = time.time()
            if now - self._hour_start >= 3600:
                self._call_count = 0
                self._hour_start = now

            if self._call_count >= 190:  # 10-call safety buffer
                wait_time = 3600 - (now - self._hour_start)
                if wait_time > 0:
                    logger.warning(f"Rate limit approaching, waiting {wait_time:.0f}s")
                    await asyncio.sleep(min(wait_time, 60))
                    self._call_count = 0
                    self._hour_start = time.time()

            self._call_count += 1

    def update_from_headers(self, headers: dict):
        """Update rate limit state from API response headers if available."""
        usage = headers.get("x-app-usage") or headers.get("x-business-use-case-usage")
        if usage:
            try:
                data = json.loads(usage) if isinstance(usage, str) else usage
                logger.debug(f"API usage: {data}")
            except (json.JSONDecodeError, TypeError):
                pass


class InstagramClient:
    """Async Instagram Graph API client."""

    def __init__(self, config: dict):
        self.config = config
        self._session = None
        self._rate_limiter = InstagramRateLimiter()

    @classmethod
    def from_config(cls, agent=None):
        """Factory: create client from A0 plugin config."""
        from usr.plugins.instagram.helpers.instagram_auth import get_instagram_config
        config = get_instagram_config(agent)
        return cls(config)

    def _get_token(self) -> str:
        from usr.plugins.instagram.helpers.instagram_auth import get_access_token
        return get_access_token(self.config)

    def _get_user_id(self) -> str:
        from usr.plugins.instagram.helpers.instagram_auth import get_ig_user_id
        return get_ig_user_id(self.config)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json_body: dict = None,
        max_retries: int = 3,
    ) -> dict:
        """
        Core API request method with rate limiting and retry.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path (e.g., "/{user_id}/media")
            params: Query parameters
            json_body: JSON body for POST requests
            max_retries: Maximum retry attempts
        """
        token = self._get_token()
        if not token:
            return {"error": True, "detail": "No access token configured"}

        url = f"{BASE_URL}{endpoint}"
        if params is None:
            params = {}
        params["access_token"] = token

        session = await self._get_session()

        for attempt in range(max_retries):
            await self._rate_limiter.wait()

            try:
                kwargs = {"params": params}
                if json_body is not None and method == "POST":
                    kwargs["json"] = json_body

                async with session.request(method, url, **kwargs) as resp:
                    self._rate_limiter.update_from_headers(dict(resp.headers))

                    # Track usage
                    from usr.plugins.instagram.helpers.instagram_auth import increment_usage
                    increment_usage(self.config, "api_calls")

                    if resp.status == 429:
                        retry_after = resp.headers.get("retry-after", "60")
                        wait = min(int(retry_after), 120) * (attempt + 1)
                        logger.warning(f"Rate limited, waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue

                    body = await resp.text()
                    if resp.status >= 400:
                        try:
                            error_data = json.loads(body)
                            error_msg = error_data.get("error", {}).get("message", body[:500])
                        except json.JSONDecodeError:
                            error_msg = body[:500]
                        return {
                            "error": True,
                            "status": resp.status,
                            "detail": error_msg,
                        }

                    if body:
                        return json.loads(body)
                    return {"ok": True}
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    err = str(e)
                    if token and token in err:
                        err = err.replace(token, "[REDACTED]")
                    return {"error": True, "detail": err}
                await asyncio.sleep(2 ** attempt)

        return {"error": True, "detail": "Max retries exceeded"}

    # --- Profile Operations ---

    async def get_me(self) -> dict:
        """Get the authenticated user's profile."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            f"/{user_id}",
            params={"fields": "id,username,name,biography,media_count,followers_count,follows_count,profile_picture_url"},
        )

    async def get_user_profile(self, user_id: str) -> dict:
        """Get a user's basic profile info by numeric ID."""
        return await self._request(
            "GET",
            f"/{user_id}",
            params={"fields": "id,username,name,biography,media_count,followers_count,follows_count,profile_picture_url"},
        )

    async def get_user_by_username(self, username: str) -> dict:
        """Look up a Business/Creator account by username via Business Discovery."""
        import re as _re
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        username = username.lstrip("@").strip()
        if not username:
            return {"error": True, "detail": "Username is required"}
        if not _re.match(r"^[a-zA-Z0-9._]{1,30}$", username):
            return {"error": True, "detail": "Invalid username format"}
        fields = "id,username,name,biography,media_count,followers_count,follows_count,profile_picture_url"
        return await self._request(
            "GET",
            f"/{user_id}",
            params={"fields": f"business_discovery.username({username}){{{fields}}}"},
        )

    # --- Media Publishing (2-step process) ---

    async def create_photo_container(self, image_url: str, caption: str = "") -> dict:
        """
        Step 1 of photo publishing: create a media container.
        Returns container with 'id' field.
        """
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        params = {
            "image_url": image_url,
        }
        if caption:
            params["caption"] = caption

        return await self._request("POST", f"/{user_id}/media", params=params)

    async def create_reel_container(self, video_url: str, caption: str = "", share_to_feed: bool = True) -> dict:
        """
        Step 1 of reel publishing: create a media container.
        """
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        params = {
            "media_type": "REELS",
            "video_url": video_url,
        }
        if caption:
            params["caption"] = caption
        if share_to_feed:
            params["share_to_feed"] = "true"

        return await self._request("POST", f"/{user_id}/media", params=params)

    async def create_carousel_item(self, image_url: str = "", video_url: str = "", is_video: bool = False) -> dict:
        """Create a child container for carousel posts."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        params = {}
        if is_video:
            params["media_type"] = "VIDEO"
            params["video_url"] = video_url
        else:
            params["image_url"] = image_url
        params["is_carousel_item"] = "true"

        return await self._request("POST", f"/{user_id}/media", params=params)

    async def create_carousel_container(self, children_ids: list, caption: str = "") -> dict:
        """
        Step 1 of carousel publishing: create the parent container.
        children_ids is a list of child container IDs.
        """
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
        }
        if caption:
            params["caption"] = caption

        return await self._request("POST", f"/{user_id}/media", params=params)

    async def publish_media(self, container_id: str) -> dict:
        """
        Step 2: Publish a media container.
        Returns the published media object with 'id' field.
        """
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        result = await self._request(
            "POST",
            f"/{user_id}/media_publish",
            params={"creation_id": container_id},
        )

        if not result.get("error"):
            from usr.plugins.instagram.helpers.instagram_auth import increment_usage
            increment_usage(self.config, "posts_published")

        return result

    async def check_container_status(self, container_id: str) -> dict:
        """Check the status of a media container (useful for video processing)."""
        return await self._request(
            "GET",
            f"/{container_id}",
            params={"fields": "status_code,status"},
        )

    # --- Media Reading ---

    async def get_media_feed(self, limit: int = 25) -> dict:
        """Get the authenticated user's media feed."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            f"/{user_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
                "limit": str(min(limit, 100)),
            },
        )

    async def get_media(self, media_id: str) -> dict:
        """Get details of a specific media post."""
        return await self._request(
            "GET",
            f"/{media_id}",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count,username",
            },
        )

    async def get_stories(self) -> dict:
        """Get the authenticated user's stories."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            f"/{user_id}/stories",
            params={"fields": "id,media_type,media_url,timestamp"},
        )

    # --- Comments ---

    async def get_comments(self, media_id: str, limit: int = 50) -> dict:
        """Get comments on a media post."""
        return await self._request(
            "GET",
            f"/{media_id}/comments",
            params={
                "fields": "id,text,username,timestamp,like_count,replies{id,text,username,timestamp}",
                "limit": str(min(limit, 100)),
            },
        )

    async def post_comment(self, media_id: str, text: str) -> dict:
        """Post a comment on a media post."""
        result = await self._request(
            "POST",
            f"/{media_id}/comments",
            params={"message": text},
        )
        if not result.get("error"):
            from usr.plugins.instagram.helpers.instagram_auth import increment_usage
            increment_usage(self.config, "comments_posted")
        return result

    async def reply_to_comment(self, comment_id: str, text: str) -> dict:
        """Reply to a specific comment."""
        result = await self._request(
            "POST",
            f"/{comment_id}/replies",
            params={"message": text},
        )
        if not result.get("error"):
            from usr.plugins.instagram.helpers.instagram_auth import increment_usage
            increment_usage(self.config, "comments_posted")
        return result

    async def delete_comment(self, comment_id: str) -> dict:
        """Delete a comment."""
        return await self._request("DELETE", f"/{comment_id}")

    # --- Hashtag Search ---

    async def search_hashtag(self, tag: str) -> dict:
        """Search for a hashtag ID."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            "/ig_hashtag_search",
            params={"q": tag, "user_id": user_id},
        )

    async def get_hashtag_recent_media(self, hashtag_id: str, limit: int = 25) -> dict:
        """Get recent media for a hashtag."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            f"/{hashtag_id}/recent_media",
            params={
                "user_id": user_id,
                "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
                "limit": str(min(limit, 50)),
            },
        )

    async def get_hashtag_top_media(self, hashtag_id: str, limit: int = 25) -> dict:
        """Get top media for a hashtag."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}
        return await self._request(
            "GET",
            f"/{hashtag_id}/top_media",
            params={
                "user_id": user_id,
                "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
                "limit": str(min(limit, 50)),
            },
        )

    # --- Insights ---

    async def get_account_insights(self, metrics: list = None, period: str = "day") -> dict:
        """Get account-level insights."""
        user_id = self._get_user_id()
        if not user_id:
            return {"error": True, "detail": "No Instagram User ID configured"}

        if metrics is None:
            metrics = ["impressions", "reach", "follower_count", "profile_views"]

        return await self._request(
            "GET",
            f"/{user_id}/insights",
            params={
                "metric": ",".join(metrics),
                "period": period,
            },
        )

    async def get_media_insights(self, media_id: str, metrics: list = None) -> dict:
        """Get insights for a specific media post."""
        if metrics is None:
            metrics = ["impressions", "reach", "engagement", "saved"]

        return await self._request(
            "GET",
            f"/{media_id}/insights",
            params={"metric": ",".join(metrics)},
        )

    # --- Media Management ---

    async def delete_media(self, media_id: str) -> dict:
        """Delete a media post (only works for posts created via the API)."""
        # Instagram Graph API doesn't support DELETE on media directly.
        # Instead, we use a workaround or note the limitation.
        # The API does not provide a delete endpoint for organic content.
        # Only content published via the Content Publishing API can be managed.
        result = await self._request("DELETE", f"/{media_id}")
        if not result.get("error"):
            from usr.plugins.instagram.helpers.instagram_auth import increment_usage
            increment_usage(self.config, "media_deleted")
        return result

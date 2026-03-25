from helpers.tool import Tool, Response


class InstagramRead(Tool):
    """Read media feed, specific posts, and stories from Instagram."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "feed")
        media_id = self.args.get("media_id", "")
        max_results = self.args.get("max_results", "25")

        from plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        from plugins.instagram.helpers.sanitize import clamp_limit
        limit = clamp_limit(max_results, default=25, maximum=100)

        from plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "feed":
                return await self._get_feed(client, limit)
            elif action == "post":
                return await self._get_post(client, media_id)
            elif action == "stories":
                return await self._get_stories(client)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: feed, post, stories",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _get_feed(self, client, limit: int) -> Response:
        self.set_progress("Fetching media feed...")
        result = await client.get_media_feed(limit)
        if result.get("error"):
            return Response(
                message=f"Error fetching feed: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        media_list = result.get("data", [])
        from plugins.instagram.helpers.sanitize import format_media_list
        formatted = format_media_list(media_list)
        count = len(media_list)
        return Response(
            message=f"Instagram feed ({count} posts):\n\n{formatted}",
            break_loop=False,
        )

    async def _get_post(self, client, media_id: str) -> Response:
        if not media_id:
            return Response(
                message="Error: 'media_id' is required. Use the feed action to find media IDs.",
                break_loop=False,
            )

        from plugins.instagram.helpers.sanitize import validate_media_id
        try:
            media_id = validate_media_id(media_id)
        except ValueError as e:
            return Response(message=f"Invalid media ID: {e}", break_loop=False)

        self.set_progress("Fetching post details...")
        result = await client.get_media(media_id)
        if result.get("error"):
            return Response(
                message=f"Error fetching post: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        from plugins.instagram.helpers.sanitize import format_media
        formatted = format_media(result)
        return Response(message=f"Post details:\n\n{formatted}", break_loop=False)

    async def _get_stories(self, client) -> Response:
        self.set_progress("Fetching stories...")
        result = await client.get_stories()
        if result.get("error"):
            return Response(
                message=f"Error fetching stories: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        stories = result.get("data", [])
        if not stories:
            return Response(message="No active stories found.", break_loop=False)

        lines = [f"Active stories ({len(stories)}):"]
        for s in stories:
            media_type = s.get("media_type", "UNKNOWN")
            timestamp = s.get("timestamp", "")[:19].replace("T", " ")
            sid = s.get("id", "")
            lines.append(f"  [{media_type}] {timestamp} (ID: {sid})")

        return Response(message="\n".join(lines), break_loop=False)

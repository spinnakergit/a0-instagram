from helpers.tool import Tool, Response


class InstagramSearch(Tool):
    """Search Instagram by hashtag and discover content."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "hashtag")
        query = self.args.get("query", "")
        sort = self.args.get("sort", "recent")
        max_results = self.args.get("max_results", "25")

        from plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        if not query:
            return Response(message="Error: 'query' is required for search.", break_loop=False)

        from plugins.instagram.helpers.sanitize import clamp_limit
        limit = clamp_limit(max_results, default=25, maximum=50)

        from plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "hashtag":
                return await self._search_hashtag(client, query, sort, limit)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: hashtag",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _search_hashtag(self, client, tag: str, sort: str, limit: int) -> Response:
        from plugins.instagram.helpers.sanitize import validate_hashtag
        try:
            tag = validate_hashtag(tag)
        except ValueError as e:
            return Response(message=f"Invalid hashtag: {e}", break_loop=False)

        self.set_progress(f"Searching #{tag}...")

        # Step 1: Get hashtag ID
        search_result = await client.search_hashtag(tag)
        if search_result.get("error"):
            return Response(
                message=f"Error searching hashtag: {search_result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        data = search_result.get("data", [])
        if not data:
            return Response(message=f"No results found for #{tag}.", break_loop=False)

        hashtag_id = data[0].get("id", "")
        if not hashtag_id:
            return Response(message=f"Could not resolve hashtag #{tag}.", break_loop=False)

        # Step 2: Get media for hashtag
        if sort == "top":
            media_result = await client.get_hashtag_top_media(hashtag_id, limit)
        else:
            media_result = await client.get_hashtag_recent_media(hashtag_id, limit)

        if media_result.get("error"):
            return Response(
                message=f"Error fetching hashtag media: {media_result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        media_list = media_result.get("data", [])
        from plugins.instagram.helpers.sanitize import format_media_list
        formatted = format_media_list(media_list)
        sort_label = "top" if sort == "top" else "recent"
        count = len(media_list)
        return Response(
            message=f"#{tag} — {sort_label} posts ({count}):\n\n{formatted}",
            break_loop=False,
        )

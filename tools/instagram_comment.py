from helpers.tool import Tool, Response


class InstagramComment(Tool):
    """List, reply to, and delete comments on Instagram posts."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "list")
        media_id = self.args.get("media_id", "")
        comment_id = self.args.get("comment_id", "")
        text = self.args.get("text", "")
        max_results = self.args.get("max_results", "50")

        from usr.plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "list":
                return await self._list_comments(client, media_id, max_results)
            elif action == "post":
                return await self._post_comment(client, media_id, text)
            elif action == "reply":
                return await self._reply_comment(client, comment_id, text)
            elif action == "delete":
                return await self._delete_comment(client, comment_id)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: list, post, reply, delete",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _list_comments(self, client, media_id: str, max_results: str) -> Response:
        if not media_id:
            return Response(
                message="Error: 'media_id' is required to list comments.",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.sanitize import validate_media_id, clamp_limit
        try:
            media_id = validate_media_id(media_id)
        except ValueError as e:
            return Response(message=f"Invalid media ID: {e}", break_loop=False)

        limit = clamp_limit(max_results, default=50, maximum=100)

        self.set_progress("Fetching comments...")
        result = await client.get_comments(media_id, limit)
        if result.get("error"):
            return Response(
                message=f"Error fetching comments: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        comments = result.get("data", [])
        from usr.plugins.instagram.helpers.sanitize import format_comments
        formatted = format_comments(comments)
        count = len(comments)
        return Response(
            message=f"Comments ({count}):\n\n{formatted}",
            break_loop=False,
        )

    async def _post_comment(self, client, media_id: str, text: str) -> Response:
        if not media_id:
            return Response(message="Error: 'media_id' is required to post a comment.", break_loop=False)
        if not text:
            return Response(message="Error: 'text' is required for the comment.", break_loop=False)

        from usr.plugins.instagram.helpers.sanitize import validate_media_id, sanitize_content
        try:
            media_id = validate_media_id(media_id)
        except ValueError as e:
            return Response(message=f"Invalid media ID: {e}", break_loop=False)

        text = sanitize_content(text, max_length=2200)
        if "[Content blocked" in text:
            return Response(message=text, break_loop=False)

        self.set_progress("Posting comment...")
        result = await client.post_comment(media_id, text)
        if result.get("error"):
            return Response(
                message=f"Error posting comment: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        comment_id = result.get("id", "unknown")
        return Response(
            message=f"Comment posted successfully.\nComment ID: {comment_id}",
            break_loop=False,
        )

    async def _reply_comment(self, client, comment_id: str, text: str) -> Response:
        if not comment_id:
            return Response(message="Error: 'comment_id' is required to reply.", break_loop=False)
        if not text:
            return Response(message="Error: 'text' is required for the reply.", break_loop=False)

        from usr.plugins.instagram.helpers.sanitize import sanitize_content, validate_media_id
        try:
            comment_id = validate_media_id(comment_id)
        except ValueError as e:
            return Response(message=f"Invalid comment ID: {e}", break_loop=False)
        text = sanitize_content(text, max_length=2200)
        if "[Content blocked" in text:
            return Response(message=text, break_loop=False)

        self.set_progress("Posting reply...")
        result = await client.reply_to_comment(comment_id, text)
        if result.get("error"):
            return Response(
                message=f"Error posting reply: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        reply_id = result.get("id", "unknown")
        return Response(
            message=f"Reply posted successfully.\nComment ID: {reply_id}",
            break_loop=False,
        )

    async def _delete_comment(self, client, comment_id: str) -> Response:
        if not comment_id:
            return Response(message="Error: 'comment_id' is required to delete.", break_loop=False)

        from usr.plugins.instagram.helpers.sanitize import validate_media_id
        try:
            comment_id = validate_media_id(comment_id)
        except ValueError as e:
            return Response(message=f"Invalid comment ID: {e}", break_loop=False)

        self.set_progress("Deleting comment...")
        result = await client.delete_comment(comment_id)
        if result.get("error"):
            return Response(
                message=f"Error deleting comment: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        return Response(message="Comment deleted successfully.", break_loop=False)

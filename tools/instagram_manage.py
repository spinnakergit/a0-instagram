from helpers.tool import Tool, Response


class InstagramManage(Tool):
    """Manage Instagram media: delete posts."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "")
        media_id = self.args.get("media_id", "")

        from plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        if not action:
            return Response(
                message="Error: 'action' is required. Use: delete",
                break_loop=False,
            )

        from plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "delete":
                return await self._delete_media(client, media_id)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: delete",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _delete_media(self, client, media_id: str) -> Response:
        return Response(
            message="The Instagram Graph API does not support deleting media posts (neither organic nor API-published). Posts must be deleted manually through the Instagram app or website.",
            break_loop=False,
        )

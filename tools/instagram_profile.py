from helpers.tool import Tool, Response


class InstagramProfile(Tool):
    """View Instagram profile information."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "me")
        user_id = self.args.get("user_id", "")
        username = self.args.get("username", "")

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
            if action == "me":
                return await self._get_my_profile(client)
            elif action == "lookup":
                if username:
                    return await self._lookup_by_username(client, username)
                return await self._lookup_profile(client, user_id)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: me, lookup",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _get_my_profile(self, client) -> Response:
        self.set_progress("Fetching your profile...")
        result = await client.get_me()
        if result.get("error"):
            return Response(
                message=f"Error fetching profile: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.sanitize import format_profile
        formatted = format_profile(result)
        return Response(message=f"Your Instagram profile:\n\n{formatted}", break_loop=False)

    async def _lookup_profile(self, client, user_id: str) -> Response:
        if not user_id:
            return Response(
                message="Error: Provide 'username' (e.g. @natgeo) or 'user_id' (numeric ID) for profile lookup.",
                break_loop=False,
            )

        self.set_progress("Fetching profile...")
        result = await client.get_user_profile(user_id)
        if result.get("error"):
            return Response(
                message=f"Error fetching profile: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.sanitize import format_profile
        formatted = format_profile(result)
        return Response(message=f"Profile:\n\n{formatted}", break_loop=False)

    async def _lookup_by_username(self, client, username: str) -> Response:
        self.set_progress(f"Looking up @{username.lstrip('@')}...")
        result = await client.get_user_by_username(username)
        if result.get("error"):
            detail = result.get("detail", "Unknown error")
            if "not found" in detail.lower() or "2069004" in str(detail):
                return Response(
                    message=f"User @{username.lstrip('@')} not found. Business Discovery only works for Business/Creator accounts.",
                    break_loop=False,
                )
            return Response(
                message=f"Error looking up @{username.lstrip('@')}: {detail}",
                break_loop=False,
            )

        profile_data = result.get("business_discovery", result)
        from usr.plugins.instagram.helpers.sanitize import format_profile
        formatted = format_profile(profile_data)
        return Response(message=f"Profile:\n\n{formatted}", break_loop=False)

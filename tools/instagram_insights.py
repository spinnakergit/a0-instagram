from helpers.tool import Tool, Response


class InstagramInsights(Tool):
    """View account and media insights from Instagram."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "account")
        media_id = self.args.get("media_id", "")
        period = self.args.get("period", "day")
        metrics = self.args.get("metrics", "")

        from plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        from plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "account":
                return await self._account_insights(client, period, metrics)
            elif action == "media":
                return await self._media_insights(client, media_id, metrics)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: account, media",
                    break_loop=False,
                )
        finally:
            await client.close()

    async def _account_insights(self, client, period: str, metrics_str: str) -> Response:
        valid_periods = ["day", "week", "days_28", "month", "lifetime"]
        if period not in valid_periods:
            return Response(
                message=f"Invalid period '{period}'. Use: {', '.join(valid_periods)}",
                break_loop=False,
            )

        metrics = None
        if metrics_str:
            metrics = [m.strip() for m in metrics_str.split(",") if m.strip()]

        self.set_progress("Fetching account insights...")
        result = await client.get_account_insights(metrics=metrics, period=period)
        if result.get("error"):
            return Response(
                message=f"Error fetching insights: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        insights_data = result.get("data", [])
        from plugins.instagram.helpers.sanitize import format_insights
        formatted = format_insights(insights_data)
        return Response(
            message=f"Account insights (period: {period}):\n\n{formatted}",
            break_loop=False,
        )

    async def _media_insights(self, client, media_id: str, metrics_str: str) -> Response:
        if not media_id:
            return Response(
                message="Error: 'media_id' is required for media insights.",
                break_loop=False,
            )

        from plugins.instagram.helpers.sanitize import validate_media_id
        try:
            media_id = validate_media_id(media_id)
        except ValueError as e:
            return Response(message=f"Invalid media ID: {e}", break_loop=False)

        metrics = None
        if metrics_str:
            metrics = [m.strip() for m in metrics_str.split(",") if m.strip()]

        self.set_progress("Fetching media insights...")
        result = await client.get_media_insights(media_id, metrics=metrics)
        if result.get("error"):
            return Response(
                message=f"Error fetching media insights: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        insights_data = result.get("data", [])
        from plugins.instagram.helpers.sanitize import format_insights
        formatted = format_insights(insights_data)
        return Response(
            message=f"Media insights (ID: {media_id}):\n\n{formatted}",
            break_loop=False,
        )

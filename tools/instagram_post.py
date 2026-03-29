from helpers.tool import Tool, Response


class InstagramPost(Tool):
    """Post photos, carousels, and reels to Instagram via the 2-step publishing flow."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "photo")
        caption = self.args.get("caption", "")
        image_url = self.args.get("image_url", "")
        video_url = self.args.get("video_url", "")
        image_urls = self.args.get("image_urls", "")  # comma-separated for carousel

        from usr.plugins.instagram.helpers.instagram_auth import get_instagram_config, has_credentials
        config = get_instagram_config(self.agent)

        if not has_credentials(config):
            return Response(
                message="Error: Instagram not configured. Set access_token and ig_user_id in plugin settings.",
                break_loop=False,
            )

        # Validate caption
        if caption:
            from usr.plugins.instagram.helpers.sanitize import sanitize_caption, validate_caption
            caption = sanitize_caption(caption)
            ok, length, issues = validate_caption(caption)
            if not ok:
                return Response(
                    message=f"Caption validation failed: {'; '.join(issues)}",
                    break_loop=False,
                )

        from usr.plugins.instagram.helpers.instagram_client import InstagramClient
        client = InstagramClient(config)

        try:
            if action == "photo":
                return await self._post_photo(client, image_url, caption)
            elif action == "reel":
                return await self._post_reel(client, video_url, caption)
            elif action == "carousel":
                return await self._post_carousel(client, image_urls, caption)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: photo, reel, carousel",
                    break_loop=False,
                )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()

    async def _post_photo(self, client, image_url: str, caption: str) -> Response:
        if not image_url:
            return Response(
                message="Error: 'image_url' is required for photo posts. Provide a publicly accessible image URL.",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.sanitize import validate_url
        image_url = validate_url(image_url)

        self.set_progress("Creating photo container...")
        container = await client.create_photo_container(image_url, caption)
        if container.get("error"):
            return Response(
                message=f"Error creating container: {container.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        container_id = container.get("id")
        if not container_id:
            return Response(message="Error: No container ID returned from API.", break_loop=False)

        self.set_progress("Publishing photo...")
        result = await client.publish_media(container_id)
        if result.get("error"):
            return Response(
                message=f"Error publishing: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        media_id = result.get("id", "unknown")
        return Response(
            message=f"Photo posted successfully.\nMedia ID: {media_id}",
            break_loop=False,
        )

    async def _post_reel(self, client, video_url: str, caption: str) -> Response:
        if not video_url:
            return Response(
                message="Error: 'video_url' is required for reel posts. Provide a publicly accessible video URL.",
                break_loop=False,
            )

        from usr.plugins.instagram.helpers.sanitize import validate_url
        video_url = validate_url(video_url)

        self.set_progress("Creating reel container...")
        container = await client.create_reel_container(video_url, caption)
        if container.get("error"):
            return Response(
                message=f"Error creating reel container: {container.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        container_id = container.get("id")
        if not container_id:
            return Response(message="Error: No container ID returned from API.", break_loop=False)

        # Reels may need processing time — poll status
        import asyncio
        self.set_progress("Waiting for video processing...")
        for _ in range(30):  # Max 5 minutes
            status = await client.check_container_status(container_id)
            status_code = status.get("status_code", "")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                return Response(
                    message=f"Reel processing failed: {status.get('status', 'Unknown error')}",
                    break_loop=False,
                )
            await asyncio.sleep(10)

        self.set_progress("Publishing reel...")
        result = await client.publish_media(container_id)
        if result.get("error"):
            return Response(
                message=f"Error publishing reel: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        media_id = result.get("id", "unknown")
        return Response(
            message=f"Reel posted successfully.\nMedia ID: {media_id}",
            break_loop=False,
        )

    async def _post_carousel(self, client, image_urls_str: str, caption: str) -> Response:
        if not image_urls_str:
            return Response(
                message="Error: 'image_urls' is required for carousel posts. Provide comma-separated publicly accessible image URLs (2-10 images).",
                break_loop=False,
            )

        urls = [u.strip() for u in image_urls_str.split(",") if u.strip()]
        if len(urls) < 2:
            return Response(message="Error: Carousel requires at least 2 images.", break_loop=False)
        if len(urls) > 10:
            return Response(message="Error: Carousel supports at most 10 items.", break_loop=False)

        from usr.plugins.instagram.helpers.sanitize import validate_url
        for url in urls:
            validate_url(url)

        # Step 1: Create child containers
        self.set_progress(f"Creating {len(urls)} carousel items...")
        children_ids = []
        for i, url in enumerate(urls):
            child = await client.create_carousel_item(image_url=url)
            if child.get("error"):
                return Response(
                    message=f"Error creating carousel item {i+1}: {child.get('detail', 'Unknown error')}",
                    break_loop=False,
                )
            child_id = child.get("id")
            if not child_id:
                return Response(message=f"Error: No ID returned for carousel item {i+1}.", break_loop=False)
            children_ids.append(child_id)

        # Step 2: Create parent container
        self.set_progress("Creating carousel container...")
        container = await client.create_carousel_container(children_ids, caption)
        if container.get("error"):
            return Response(
                message=f"Error creating carousel: {container.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        container_id = container.get("id")
        if not container_id:
            return Response(message="Error: No carousel container ID returned.", break_loop=False)

        # Step 3: Publish
        self.set_progress("Publishing carousel...")
        result = await client.publish_media(container_id)
        if result.get("error"):
            return Response(
                message=f"Error publishing carousel: {result.get('detail', 'Unknown error')}",
                break_loop=False,
            )

        media_id = result.get("id", "unknown")
        return Response(
            message=f"Carousel posted successfully ({len(urls)} items).\nMedia ID: {media_id}",
            break_loop=False,
        )

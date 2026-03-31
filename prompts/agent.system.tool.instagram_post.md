## instagram_post
Post photos, carousels, and reels to Instagram.

**IMPORTANT:** Pass the original image/video URL directly to this tool EXACTLY as provided by the user. Do NOT download, re-upload, re-host (e.g. to imgur), or transform the media URL in any way — Instagram's API fetches the URL server-side. The URL must be publicly accessible on the internet. GitHub raw URLs, direct image links, and CDN URLs all work.

**Requires:** Business/Creator account with instagram_content_publish permission

**Arguments:**
- **action** (string): "photo" (default), "reel", or "carousel"
- **caption** (string): Post caption (max 2,200 characters, max 30 hashtags)
- **image_url** (string): Publicly accessible image URL — pass directly, do not download (for photo)
- **video_url** (string): Publicly accessible video URL — pass directly, do not download (for reel)
- **image_urls** (string): Comma-separated image URLs (for carousel, 2-10 items)

~~~json
{"action": "photo", "image_url": "https://example.com/photo.jpg", "caption": "Beautiful sunset! #nature"}
~~~
~~~json
{"action": "reel", "video_url": "https://example.com/video.mp4", "caption": "Check this out!"}
~~~
~~~json
{"action": "carousel", "image_urls": "https://example.com/1.jpg,https://example.com/2.jpg", "caption": "Photo series"}
~~~

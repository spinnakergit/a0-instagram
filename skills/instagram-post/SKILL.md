---
name: "instagram-post"
description: "Publish photos, carousels, and reels to Instagram."
version: "1.0.0"
author: "AgentZero Instagram Plugin"
license: "MIT"
tags: ["instagram", "post", "publish", "social-media"]
triggers:
  - "post to instagram"
  - "instagram post"
  - "share on instagram"
  - "publish to instagram"
  - "upload to instagram"
allowed_tools:
  - instagram_post
  - instagram_read
metadata:
  complexity: "basic"
  category: "publishing"
---

# Instagram Post Skill

Publish photos, carousels, and reels to Instagram.

## Workflow

### Post a Photo
```json
{"tool": "instagram_post", "args": {"action": "photo", "image_url": "https://example.com/photo.jpg", "caption": "Check this out! #amazing"}}
```

### Post a Carousel
```json
{"tool": "instagram_post", "args": {"action": "carousel", "image_urls": "https://example.com/1.jpg,https://example.com/2.jpg,https://example.com/3.jpg", "caption": "Photo series!"}}
```

### Post a Reel
```json
{"tool": "instagram_post", "args": {"action": "reel", "video_url": "https://example.com/video.mp4", "caption": "New reel!"}}
```

## Tips
- Images and videos must be publicly accessible URLs
- Captions can be up to 2,200 characters with up to 30 hashtags
- Reel videos may take time to process before publishing
- Carousels need 2-10 items
- Use `instagram_read` to verify your post after publishing

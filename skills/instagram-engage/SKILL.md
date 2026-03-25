---
name: "instagram-engage"
description: "Engage with Instagram content by commenting and replying to comments."
version: "1.0.0"
author: "AgentZero Instagram Plugin"
license: "MIT"
tags: ["instagram", "comments", "engagement", "social"]
triggers:
  - "instagram comment"
  - "reply instagram"
  - "engage instagram"
  - "instagram engagement"
allowed_tools:
  - instagram_comment
  - instagram_read
metadata:
  complexity: "basic"
  category: "engagement"
---

# Instagram Engagement Skill

Engage with your Instagram audience by managing comments.

## Workflow

### Step 1: Find a Post
```json
{"tool": "instagram_read", "args": {"action": "feed"}}
```

### Step 2: Read Comments
```json
{"tool": "instagram_comment", "args": {"action": "list", "media_id": "17895695668004550"}}
```

### Step 3: Reply to a Comment
```json
{"tool": "instagram_comment", "args": {"action": "reply", "comment_id": "17858893269000001", "text": "Thanks for the feedback!"}}
```

### Post a New Comment
```json
{"tool": "instagram_comment", "args": {"action": "post", "media_id": "17895695668004550", "text": "Great content!"}}
```

## Tips
- Comments are limited to 2,200 characters
- Use the feed tool to find media IDs, then list comments on those posts
- You can delete your own comments using the delete action
- Replying to comments creates a threaded reply under the original comment

## instagram_comment
List, post, reply to, and delete comments on Instagram posts.

**Requires:** Business/Creator account with instagram_manage_comments permission

**Arguments:**
- **action** (string): "list" (default), "post", "reply", or "delete"
- **media_id** (string): Media ID (for "list" and "post" actions)
- **comment_id** (string): Comment ID (for "reply" and "delete" actions)
- **text** (string): Comment text (for "post" and "reply", max 2,200 characters)
- **max_results** (string): Number of comments to list (default: "50")

~~~json
{"action": "list", "media_id": "17895695668004550"}
~~~
~~~json
{"action": "post", "media_id": "17895695668004550", "text": "Great photo!"}
~~~
~~~json
{"action": "reply", "comment_id": "17858893269000001", "text": "Thanks!"}
~~~
~~~json
{"action": "delete", "comment_id": "17858893269000001"}
~~~

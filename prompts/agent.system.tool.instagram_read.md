## instagram_read
Read media feed, specific posts, and stories from Instagram.

**Requires:** Business/Creator account with instagram_basic permission

**Arguments:**
- **action** (string): "feed" (default), "post", or "stories"
- **media_id** (string): Media ID for "post" action
- **max_results** (string): Number of results for feed (default: "25", max: 100)

~~~json
{"action": "feed"}
~~~
~~~json
{"action": "feed", "max_results": "10"}
~~~
~~~json
{"action": "post", "media_id": "17895695668004550"}
~~~
~~~json
{"action": "stories"}
~~~

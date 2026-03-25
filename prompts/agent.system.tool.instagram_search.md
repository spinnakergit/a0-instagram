## instagram_search
Search Instagram by hashtag to discover content.

**Requires:** Business/Creator account with instagram_basic permission
**Note:** Limited to 30 unique hashtag searches per 7-day rolling window.

**Arguments:**
- **action** (string): "hashtag" (default)
- **query** (string, required): Hashtag to search (without #)
- **sort** (string): "recent" (default) or "top"
- **max_results** (string): Number of results (default: "25", max: 50)

~~~json
{"action": "hashtag", "query": "photography", "sort": "top"}
~~~
~~~json
{"action": "hashtag", "query": "sunset", "max_results": "10"}
~~~

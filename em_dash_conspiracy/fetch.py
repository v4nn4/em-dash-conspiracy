import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import praw


def fetch_top_posts(sub: str, reddit: praw.Reddit) -> List[dict]:
    """Fetch top posts from the last year for a given subreddit."""
    posts = []
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    try:
        for post in reddit.subreddit(sub).top(limit=1000, time_filter="year"):
            created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
            if created < one_year_ago:
                continue
            posts.append(
                {
                    "subreddit": sub,
                    "selftext": post.selftext or "",
                    "created_utc": created,
                }
            )
    except Exception as e:
        print(f"❌ Error fetching r/{sub}: {e}")

    return posts


def fetch_subs(
    keywords: List[str],
    reddit: praw.Reddit,
    min_subs: int = 100_000,
    limit: int = 100,
    outfile: str = "subs.json",
    save: bool = False,
) -> List[dict]:
    """Find unique subreddits matching keyword queries with subscriber thresholds."""
    seen = {}

    for keyword in keywords:
        print(f"🔍 Searching for subreddits matching '{keyword}'...")
        try:
            for sub in reddit.subreddits.search(keyword, limit=limit):
                is_text_allowed = sub.submission_type in ("self", "any")

                if not is_text_allowed or sub.over18 or sub.quarantine:
                    continue

                if not sub.subscribers or sub.subscribers < min_subs:
                    continue

                name = sub.display_name
                if name not in seen:
                    seen[name] = {
                        "name": name,
                        "subscribers": sub.subscribers,
                        "title": sub.title,
                        "description": sub.public_description,
                        "created_utc": sub.created_utc,
                        "matched_keywords": [keyword],
                    }
                else:
                    seen[name]["matched_keywords"].append(keyword)
        except Exception as e:
            print(f"❌ Error with keyword '{keyword}': {e}")

    subreddits = list(seen.values())

    if save:
        Path(outfile).write_text(json.dumps(subreddits, indent=2))
        print(f"💾 Saved {len(subreddits)} subreddits to {outfile}")

    return subreddits

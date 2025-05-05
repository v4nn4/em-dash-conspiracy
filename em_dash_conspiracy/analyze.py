import json
from pathlib import Path
from typing import Union

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from em_dash_conspiracy.fetch import fetch_top_posts


def analyze_em_dash_usage(
    reddit,
    infile: Union[str, Path] = "subs.json",
    outfile: Union[str, Path] = "analysis.csv",
    max_workers: int = 8,
    save: bool = True,
) -> pd.DataFrame:
    """Analyze em-dash usage in top posts across subreddits over the past year, with examples."""

    subs_data = json.loads(Path(infile).read_text())
    subreddit_names = {sub["name"] for sub in subs_data}

    all_posts = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_top_posts, sub, reddit): sub
            for sub in list(subreddit_names)
        }
        fixed_width = max(len(sub) for sub in subreddit_names) + 2
        with tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"Fetching posts from su{'breddits'.ljust(fixed_width)}",
        ) as pbar:
            for future in pbar:
                current_subreddit = futures[future]
                padded_subreddit_name = current_subreddit.ljust(fixed_width)
                pbar.set_description(f"Fetching posts from r/{padded_subreddit_name}")
                all_posts.extend(future.result())

    df = pd.DataFrame(all_posts)
    df["selftext"] = df["selftext"].fillna("").str.strip()
    df = df[~df["selftext"].isin({"", "[removed]", "[deleted]"})]

    df["created_utc"] = pd.to_datetime(df["created_utc"]).dt.tz_localize(None)
    df["month"] = df["created_utc"].dt.to_period("M").dt.to_timestamp()
    df["has_emdash"] = df["selftext"].str.contains("—")

    # Extract example em-dash sentences
    def extract_last_emdash_sentence(text: str) -> str:
        if not isinstance(text, str) or "—" not in text:
            return ""
        # Naively split on sentence terminators
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if "—" in s]
        return sentences[-1] if sentences else ""

    df["emdash_example"] = df["selftext"].apply(extract_last_emdash_sentence)

    summary = (
        df.groupby(["subreddit", "month"])
        .agg(
            num_posts=("selftext", "count"),
            num_emdash=("has_emdash", "sum"),
            last_emdash_example=(
                "emdash_example",
                lambda x: next((s for s in reversed(list(x)) if s), ""),
            ),
        )
        .reset_index()
    )

    summary["emdash_percent"] = 100 * summary["num_emdash"] / summary["num_posts"]
    summary = summary.sort_values(["subreddit", "month"])

    if save:
        Path(outfile).write_text(summary.to_csv(index=False))
        print(f"💾 Saved analysis to {outfile}")

    return summary

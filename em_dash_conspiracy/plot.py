import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import PercentFormatter

# https://iamkate.com/data/12-bit-rainbow/
PALETTE = [
    "#817",
    "#a35",
    "#c66",
    "#e94",
    "#ed0",
    "#9d5",
    "#4d8",
    "#2cb",
    "#0bc",
    "#09c",
    "#36b",
    "#639",
]


def fmt(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def plot_em_dash_usage(
    sub_names: list[str], analysis_file: str, subs_file: str, outfile: str
):
    """Plot em dash usage for selected subreddits over time."""
    df = pd.read_csv(analysis_file)
    df["month"] = pd.to_datetime(df["month"])
    df = df[df["month"] != pd.to_datetime("2025-01-01")]

    subs = json.loads(Path(subs_file).read_text())
    sub_counts = {s["name"]: s["subscribers"] for s in subs}
    available = set(sub_counts)

    missing = [name for name in sub_names if name not in available]
    if missing:
        raise ValueError(f"Subreddits not found in subs file: {', '.join(missing)}")

    names = sorted(sub_names, key=lambda s: sub_counts.get(s, 0), reverse=True)
    df = df[df["subreddit"].isin(names)]

    with plt.xkcd():
        fig, ax = plt.subplots(figsize=(8, 6))
        for i, name in enumerate(names):
            d = df[df["subreddit"] == name].sort_values("month").copy()
            d["y"] = d["em_dash_percent"].rolling(2, min_periods=1).mean()
            ax.plot(
                d["month"],
                d["y"],
                label=f"r/{name} ({fmt(sub_counts.get(name, 0))})",
                color=PALETTE[i % len(PALETTE)],
                lw=2.5,
            )

        ax.set_title("The Em Dash (—) Conspiracy", fontsize=16)
        ax.set_ylabel("% of Posts Using Em Dash (—)", fontsize=14)
        ax.set_xlabel("Month")
        ax.set_ylim(0, 20)
        ax.set_yticks([0, 5, 10, 15, 20])
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.xaxis.set_major_formatter(DateFormatter("%b %y"))
        ax.legend(title="Subreddit", fontsize=12)
        ax.text(
            0.99,
            0.02,
            "Source: Reddit API — Data as of 4 May 2025",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=9,
            color="gray",
        )

        plt.subplots_adjust(bottom=0.2)

        plt.tight_layout()
        plt.savefig(outfile, dpi=300)

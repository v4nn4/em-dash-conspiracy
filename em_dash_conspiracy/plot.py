import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

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

        ax.set_title("The Em Dash Conspiracy", fontsize=16)
        ax.set_ylabel("Share of Posts Using Em Dash")
        ax.set_xlabel("Month")
        ax.xaxis.set_major_formatter(DateFormatter("%b %y"))  # <- Add this line
        ax.legend(title="Subreddit", fontsize=12)
        plt.tight_layout()
        plt.savefig(outfile, dpi=300)

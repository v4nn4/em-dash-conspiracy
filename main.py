import os
from pathlib import Path
import fire
import praw
from dotenv import load_dotenv

from em_dash_conspiracy.plot import plot_em_dash_usage
from em_dash_conspiracy.analyze import analyze_em_dash_usage
from em_dash_conspiracy.fetch import fetch_subs


load_dotenv()


class Paths:
    root = Path("data")
    subs = root / "subs.json"
    analysis = root / "analysis.csv"
    plot = root / "plot.png"


CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "em-dash-analyzer"

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
)


class Cli:
    def prepare(
        self, keywords: str = "ai,machine learning,data,programming,webdev,startups"
    ):
        fetch_subs(keywords.split(","), reddit, save=True, outfile=Paths.subs)

    def analyze(self):
        analyze_em_dash_usage(reddit, infile=Paths.subs, outfile=Paths.analysis)

    def plot(
        self,
        sub_names: str = "SaaS,SideProject,EntrepreneurRideAlong,Entrepreneur,startups,Startup_Ideas",
    ):
        plot_em_dash_usage(
            sub_names=sub_names.split(","),
            analysis_file=Paths.analysis,
            subs_file=Paths.subs,
            outfile=Paths.plot,
        )


if __name__ == "__main__":
    fire.Fire(Cli)

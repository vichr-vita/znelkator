from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
from typing import List, Optional, Dict
import re
import random
import pandas as pd
from datetime import datetime


@dataclass
class TuneLink:
    link_name: str
    link_url: str
    difficulty: Optional[str] = None


@dataclass
class Tune:
    name: str
    links: Optional[List[TuneLink]]


def parse_tunes(file_path: str) -> List[Tune]:
    with open(file_path, "r") as file:
        content = file.read()

    soup = BeautifulSoup(content, "html.parser")

    tunes = []
    outer_ol = soup.find("ol")

    if not isinstance(outer_ol, Tag):
        raise ValueError(f"Could not find the outer <ol> element in {file_path}")

    for li in outer_ol.find_all("li", recursive=False):
        tune_name = li.text.split("\n")[0]
        tune_links = []
        inner_ol = li.find("ol")
        if inner_ol:
            for inner_li in inner_ol.find_all("li", recursive=False):
                url = inner_li.find("a")["href"]
                link_parts = inner_li.text.split("\n")
                link = link_parts[0]
                difficulty = None
                difficulty = link[
                    -1
                ]  # this is a naive way to do things but it works atm
                link = link[:-2]
                tune_links.append(TuneLink(link, url, difficulty))
        if len(tune_links) == 0:
            tune_links = None
        tunes.append(Tune(tune_name, tune_links))

    return tunes


@dataclass
class GeneratedTune:
    tune_name: str
    link_name: str
    link_url: str
    difficulty: Optional[str] = None

    def __str__(self):
        return (
            f"{self.tune_name} - {self.link_name} ({self.difficulty}) - {self.link_url}"
        )


def generate_tune_links(
    tunes: List[Tune], diffs: Dict[int, int]
) -> List[GeneratedTune]:
    """generate a list of links to tunes


    Args:
        tunes: tunes list
        diffs: dict[difficulty: count]

    Returns:
        list of generated links
    """
    generated_tunes: List[GeneratedTune] = []
    used_links = set()

    # Distribute the difficulties
    for diff, count in diffs.items():
        picked_counter = 0
        while picked_counter < count:
            # Randomly select a tune
            tune = random.choice(tunes)
            if tune.links is not None:
                # Randomly select a link
                link = random.choice(tune.links)

                if link.difficulty != str(diff):
                    continue
                if link.link_url not in used_links:
                    # Set the difficulty and add the link to the list
                    generated_tunes.append(
                        GeneratedTune(
                            tune.name, link.link_name, link.link_url, link.difficulty
                        )
                    )
                    used_links.add(link.link_url)
                    picked_counter += 1
                else:
                    # Try again
                    print(f"Link {link.link_name} already used, trying again")

    return generated_tunes


def tunes_to_dataframe(tunes: List[GeneratedTune]) -> pd.DataFrame:
    data = []
    for tune in tunes:
        # Convert each GeneratedTune instance to a dict
        data.append(tune.__dict__)

    # Use the list of dicts to create a DataFrame
    df = pd.DataFrame(data)

    return df


# example usage
tunes = parse_tunes("znelky.html")
diffs = {1: 15, 2: 7, 3: 3}

links = generate_tune_links(tunes, diffs)

df = tunes_to_dataframe(links)

# Get the current time and format it as an ISO 8601 string
timestamp = datetime.now().isoformat()

# Replace colons with underscores (or use another character)
timestamp = timestamp.replace(":", "-")

# Append the timestamp to your filename
excel_export_filename = f"out/znelkator_export_{timestamp}.xlsx"


# to excel
df.to_excel(excel_export_filename, index=False)

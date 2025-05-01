import json
import argparse
import re
import logging
import os
from pathlib import Path
from datetime import datetime

# Constants
FAVORITES_SECTION = "favorites"
UNSORTED_SECTION = "unsorted"

CATEGORY_ID_MAP = {
    0: "unsorted",
    1: "live-channels",
    2: "movies",
    3: "series",
    4: "4k-movies",
    5: "box-sets",
    6: "live-sports",
    7: "kids-movies",
    8: "kids-series",
    9: "music-events",
    10: "24/7",
    99: "favorites"
}

DATA_FOLDER = Path("../data")
HTML_FOLDER = Path("../html")
ROOT_FOLDER = Path("../")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def ensure_folder_structure():
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    HTML_FOLDER.mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured folders: {DATA_FOLDER} and {HTML_FOLDER}")

def resolve_data_path(filename):
    path = Path(filename)
    if not path.is_absolute() and not str(path).startswith(str(DATA_FOLDER)):
        return DATA_FOLDER / path
    return path

def extract_group_titles_and_counts_from_m3u(m3u_path):
    groups = {}
    total_channels = 0
    if not m3u_path.exists():
        logging.error(f"M3U file does not exist: {m3u_path}")
        return {}, 0

    with m3u_path.open('r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r'group-title="([^"]+)', line)
            if match:
                title = match.group(1).strip()
                groups[title] = groups.get(title, 0) + 1
                total_channels += 1
    return groups, total_channels

def backup_file(file_path):
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    if file_path.exists():
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        logging.info(f"Created backup: {backup_path}")

def create_readme_files():
    readme_md_content = """# IPTV Project

## Folder Structure

```text
iptv/
├── cfg-handler/
│   ├── cfg-handler.py
│   └── readme.txt
├── data/
│   ├── iptv.m3u
│   ├── output.cfg
├── html/
│   ├── index.html
│   ├── style.css
│   └── script.js
```
"""
    (ROOT_FOLDER / "README.md").write_text(readme_md_content, encoding='utf-8')
    logging.info("Created README.md")

    readme_txt_content = """IPTV Config Handler - README

Program Flow:
1. Start by creating a .cfg file from your .m3u playlist.
2. Edit the .cfg file manually.
3. Use --sort to clean and categorize the config based on 'category-id'.

Category-ID Mapping:
- 0: Unsorted
- 1: Live Channels
- 2: Movies
- 3: Series
- 4: 4K Movies
- 5: Box Sets
- 6: Live Sports
- 7: Kids Movies
- 8: Kids Series
- 9: Music Events
- 10: 24/7 Channels
- 99: Favorites

Example Usage:
- Create config: python cfg-handler.py -i iptv.m3u -c output.cfg
- Sort config:   python cfg-handler.py --sort -c output.cfg
"""
    (Path(__file__).parent / "readme.txt").write_text(readme_txt_content, encoding='utf-8')
    logging.info("Created readme.txt")

def create_cfg_file(m3u_path, output_cfg):
    ensure_folder_structure()
    groups, total_channels = extract_group_titles_and_counts_from_m3u(m3u_path)

    unsorted = [
        {
            "source-group-title": title,
            "custom-group-title": title,
            "include-in-export": False,
            "channel-count": count,
            "category-id": 0
        }
        for title, count in sorted(groups.items())
    ]

    cfg_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "group-count": len(groups),
        "channel-count-total": total_channels,
        **{v: [] for k, v in CATEGORY_ID_MAP.items() if v not in (FAVORITES_SECTION, UNSORTED_SECTION)},
        FAVORITES_SECTION: [],
        UNSORTED_SECTION: unsorted
    }

    output_path = resolve_data_path(output_cfg)
    output_path.write_text(json.dumps(cfg_data, indent=4, ensure_ascii=False), encoding='utf-8')
    logging.info(f"Created config file: {output_path}")

    create_readme_files()

def sort_cfg_file(cfg_path):
    full_path = resolve_data_path(cfg_path)
    backup_file(full_path)

    with full_path.open('r', encoding='utf-8') as f:
        cfg = json.load(f)

    categorized = {name: [] for name in CATEGORY_ID_MAP.values() if name not in (FAVORITES_SECTION, UNSORTED_SECTION)}
    favorites = []
    unsorted = []

    all_entries = [entry for key, entries in cfg.items() if isinstance(entries, list) for entry in entries]

    for entry in all_entries:
        cleaned = {
            "source-group-title": entry.get("source-group-title", ""),
            "custom-group-title": entry.get("custom-group-title", ""),
            "include-in-export": entry.get("include-in-export", False),
            "channel-count": entry.get("channel-count", 0),
            "category-id": entry.get("category-id", 0)
        }

        category_id = cleaned.get("category-id", 0)

        if category_id == 99:
            favorites.append(cleaned)
        elif category_id in CATEGORY_ID_MAP and CATEGORY_ID_MAP[category_id] in categorized:
            categorized[CATEGORY_ID_MAP[category_id]].append(cleaned)
        else:
            cleaned["category-id"] = 0
            unsorted.append(cleaned)

    # Sort entries alphabetically
    for group in categorized.values():
        group.sort(key=lambda x: x["custom-group-title"])
    favorites.sort(key=lambda x: x["custom-group-title"])
    unsorted.sort(key=lambda x: x["custom-group-title"])

    result = {
        "date": cfg.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "group-count": cfg.get("group-count", 0),
        "channel-count-total": cfg.get("channel-count-total", 0),
        **categorized,
        FAVORITES_SECTION: favorites,
        UNSORTED_SECTION: unsorted
    }

    full_path.write_text(json.dumps(result, indent=4, ensure_ascii=False), encoding='utf-8')
    logging.info(f"Sorted config file: {full_path}")

    # Export JSON for HTML editor
    json_export_path = resolve_data_path("output.json")
    json_export_path.write_text(json.dumps(result, indent=4, ensure_ascii=False), encoding='utf-8')
    logging.info(f"Exported sorted JSON for HTML editor at: {json_export_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
IPTV Config Handler:

Examples:
- Create cfg: python cfg-handler.py -i iptv.m3u -c output.cfg
- Sort cfg:   python cfg-handler.py -s -c output.cfg
""", formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-i", "--m3u", help="Path to input M3U file", required=False)
    parser.add_argument("-c", "--cfg", help="Path to config (.cfg) file", required=True)
    parser.add_argument("-s", "--sort", action="store_true", help="Sort existing .cfg file into categories")

    args = parser.parse_args()

    if args.sort:
        sort_cfg_file(args.cfg)
    elif args.m3u:
        create_cfg_file(resolve_data_path(args.m3u), args.cfg)
    else:
        parser.error("You must provide either -i/--m3u to create or -s/--sort to sort a .cfg file.")

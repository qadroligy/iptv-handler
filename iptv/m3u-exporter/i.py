import argparse
import json
import re
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REMOVE_TERMS = [
    r"\[SE\]", r"\[Multi-Sub\]", r"\\d+x\\d+", r"\\(\\d{4}\\)", r"\\[\\d{4}\\]",
    r"\\(.*?\\)", r"\(\d{4}\)", r"\d{4}", r"\s{2,}"
]

EXCEPTION_TITLES = {"90210", "1923"}

FAVORITES_SECTION = "__favorites__"
NON_FAVORITES_SECTION = "__nonfavorites__"

def clean_show_name(show_name):
    original_name = show_name
    for term in REMOVE_TERMS:
        try:
            show_name = re.sub(term, '', show_name)
        except re.error as e:
            logging.error(f"Regex error with term '{term}': {e}")

    if original_name.strip() in EXCEPTION_TITLES:
        return original_name.strip()

    show_name = re.sub(r'S\d{2}', '', show_name)
    show_name = re.sub(r'E\d{2}', '', show_name)
    show_name = re.sub(r'(?<= )-', '', show_name)
    show_name = re.sub(r'\s+', ' ', show_name).strip()

    words = show_name.split()
    seen = set()
    unique_words = []
    for word in words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)

    return " ".join(unique_words).strip()

def clean_season_episode(tvg_name):
    match = re.search(r'S(\d{2})E(\d{2})', tvg_name, re.IGNORECASE)
    if match:
        season = f"S{match.group(1)}"
        episode = f"E{match.group(2)}"
        compact = season + episode
    else:
        match = re.search(r'(\d{1,2})[xX](\d{2})', tvg_name)
        if match:
            season = f"S{int(match.group(1)):02d}"
            episode = f"E{int(match.group(2)):02d}"
            compact = season + episode
        else:
            match = re.search(r'\b(\d)(\d{2})\b', tvg_name)
            if match:
                season = f"S{int(match.group(1)):02d}"
                episode = f"E{int(match.group(2)):02d}"
                compact = season + episode
            else:
                season = episode = compact = None
    return season, episode, compact

def create_config_file(group_titles, config_file):
    group_titles = {title for title in group_titles if title.strip()}
    nonfavorites = [
        {"grp-title-orginal": group, "grp-title-changed": group, "add-to-m3u": False} for group in sorted(group_titles)
    ]
    result = {FAVORITES_SECTION: [], NON_FAVORITES_SECTION: nonfavorites}
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(result, file, indent=4, ensure_ascii=False)
    logging.info(f"Config file created: {config_file}")

def clean_config_duplicates(cfg_file):
    with open(cfg_file, 'r', encoding='utf-8') as f:
        cfg_data = json.load(f)

    favorites = []
    nonfavorites = []

    for section in (cfg_data.get(FAVORITES_SECTION, []) + cfg_data.get(NON_FAVORITES_SECTION, [])):
        enabled = section.get("add-to-m3u", False)
        entry = {
            "grp-title-orginal": section.get("grp-title-orginal", section.get("original", "")),
            "grp-title-changed": section.get("grp-title-changed", section.get("rename", "")),
            "add-to-m3u": enabled
        }
        if enabled:
            favorites.append(entry)
        else:
            nonfavorites.append(entry)

    ordered_cfg = {
        FAVORITES_SECTION: sorted(favorites, key=lambda x: x["grp-title-changed"]),
        NON_FAVORITES_SECTION: sorted(nonfavorites, key=lambda x: x["grp-title-changed"])
    }

    with open(cfg_file, 'w', encoding='utf-8') as f:
        json.dump(ordered_cfg, f, indent=4, ensure_ascii=False)
    logging.info(f"Cleaned and rearranged config file: {cfg_file}")

def parse_cfg_filter(cfg_file):
    with open(cfg_file, 'r', encoding='utf-8') as file:
        cfg_data = json.load(file)
    cfg_filter = {}
    favorite_groups = set()
    favorite_originals = {}

    for entry in cfg_data.get(FAVORITES_SECTION, []):
        if entry.get("add-to-m3u"):
            orig = entry.get("grp-title-orginal", "")
            renamed = entry.get("grp-title-changed", orig)
            cfg_filter[orig] = renamed
            favorite_groups.add(renamed)
            favorite_originals[renamed] = orig

    return (cfg_filter, favorite_groups, favorite_originals)

def parse_m3u_to_json(file_path, cfg_filter_data=None):
    if cfg_filter_data:
        cfg_filter, favorite_groups, favorite_originals = cfg_filter_data
    else:
        cfg_filter, favorite_groups, favorite_originals = ({}, set(), {})

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = []
    group_titles = set()
    group_map = {}
    current_item = {}

    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            tvg_name_match = re.search(r'tvg-name="([^"]+)', line)
            tvg_logo_match = re.search(r'tvg-logo="([^"]+)', line)
            group_title_match = re.search(r'group-title="([^"]+)', line)
            tvg_id_match = re.search(r'tvg-id="([^"]+)', line)

            tvg_name = tvg_name_match.group(1) if tvg_name_match else ''
            tvg_logo = tvg_logo_match.group(1) if tvg_logo_match else ''
            group_title = group_title_match.group(1) if group_title_match else ''
            tvg_id = tvg_id_match.group(1) if tvg_id_match else None

            group_titles.add(group_title)
            group_map.setdefault(group_title, []).append((tvg_name, tvg_logo, tvg_id))

        elif line.startswith('http') and current_item:
            current_item['url'] = line
            data.append(current_item)
            current_item = {}

    filtered_data = []
    for orig_group, renamed_group in cfg_filter.items():
        for entry in group_map.get(orig_group, []):
            tvg_name, tvg_logo, tvg_id = entry
            show_name = tvg_name

            if show_name in EXCEPTION_TITLES:
                year = None
            else:
                year_match = re.search(r'[\[(](\d{4})[\])]', tvg_name)
                if not year_match:
                    year_match = re.search(r'(\d{4})', tvg_name)
                year = year_match.group(1) if year_match else None

            season, episode, compact = clean_season_episode(tvg_name)
            current_item = {
                "tvg-original": tvg_name if show_name not in EXCEPTION_TITLES else show_name,
                "tvg-title": "" if show_name in EXCEPTION_TITLES else show_name,
                "tvg-season": season,
                "tvg-episode": episode,
                "tvg-compact": compact,
                "tvg-logo": tvg_logo,
                "grp-title-orginal": orig_group,
                "grp-title-changed": renamed_group,
                "tvg-year": None if show_name in EXCEPTION_TITLES else year,
                "tvg-id": tvg_id,
                "url": ""
            }
            filtered_data.append(current_item)

    return {
        "datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "m3u-list": os.path.basename(file_path),
        "tvg-items": list(cfg_filter.keys()),
        "tvg-data": filtered_data
    }




# Remaining parts (like main and m3u generation) stay unchanged

def main():
    parser = argparse.ArgumentParser(description="M3U to JSON converter with optional filtering and config generation.")
    parser.add_argument('-i', '--input', type=str, required='--clean-cfg' not in sys.argv, help='Input M3U file.')
    parser.add_argument('-o', '--output', type=str, help='Output file basename (without extension).')
    parser.add_argument('-c', '--config', type=str, help='Create a configuration file from group titles.')
    parser.add_argument('--cfg-filter', '-f', type=str, help='Path to cfg file for group-title filtering.')
    parser.add_argument('--no-output', action='store_true', help='Skip writing .json and .m3u output files.')
    parser.add_argument('--clean-cfg', action='store_true', help='Clean duplicates from the config file.')
    args = parser.parse_args()

    if args.clean_cfg and args.cfg_filter:
        clean_config_duplicates(args.cfg_filter)
        return

    cfg_filter_data = parse_cfg_filter(args.cfg_filter) if args.cfg_filter else None
    parsed_data = parse_m3u_to_json(args.input, cfg_filter_data)

    if args.config:
        create_config_file(parsed_data["tvg-items"], args.config)
        return

    if args.no_output:
        logging.info("Skipping output file generation (--no-output enabled).")
        return

    if args.output:
        json_output = args.output + '.json'
        m3u_output = args.output + '.m3u'
    else:
        base = os.path.splitext(args.input)[0] + 'v2'
        json_output = base + '.json'
        m3u_output = base + '.m3u'

    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=4, ensure_ascii=False)
    logging.info(f"JSON output written to {json_output}")

    parse_json_to_m3u(parsed_data, m3u_output)

def parse_json_to_m3u(parsed_data, output_file):
    m3u_content = "#EXTM3U\n"
    for item in parsed_data['tvg-data']:
        tvg_clean = item.get("tvg-title", "")
        tvg_logo = item.get("tvg-logo", "")
        group_title = item.get("group-title", "")
        tvg_id = item.get("tvg-id", "")
        tvg_year = item.get("tvg-year", "")
        tvg_compact = item.get("tvg-compact", "")

        if tvg_compact:
            title = f"{tvg_clean} ({tvg_year}) ({tvg_compact})" if tvg_year else f"{tvg_clean} ({tvg_compact})"
        else:
            title = f"{tvg_clean} ({tvg_year})" if tvg_year else tvg_clean

        extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{title}" tvg-logo="{tvg_logo}" group-title="{group_title}",{title}\n'
        url = item.get("url", "")
        m3u_content += extinf + url + "\n"

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(m3u_content)
    logging.info(f"M3U output written to {output_file}")

if __name__ == '__main__':
    main()

"""
Hilfsfunktionen für Segment-Metadaten, Dateinamen, Datumsextraktion
"""

import re
from collections import OrderedDict


def extract_date_from_filename(filename):
    if not isinstance(filename, (str, bytes)):
        return None

    match = re.search(r'DJI_(\d{8})\d{6}', filename)
    if match:
        return match.group(1)
    match2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if match2:
        year, month, day = match2.groups()
        return f"{year}{month}{day}"

    return None

def format_date_ddmmyyyy(yyyymmdd):
    if not yyyymmdd or len(yyyymmdd) != 8:
        return None
    year = yyyymmdd[0:4]
    month = yyyymmdd[4:6]
    day = yyyymmdd[6:8]

    return f"{day}_{month}_{year}"

def generate_output_filename(segments, output_base_dir="output"):
    dates = set()
    for seg in segments:
        videoname = seg.get('videoname', None)
        if not videoname:
            continue
        date = extract_date_from_filename(videoname)
        if date:
            dates.add(date)
    sorted_dates = sorted(dates)
    formatted_dates = []
    for d in sorted_dates:
        formatted = format_date_ddmmyyyy(d)
        if formatted:
            formatted_dates.append(formatted)
    if not formatted_dates:
        return f"{output_base_dir}/Spielanalyse.mp4"
    date_string = "_".join(formatted_dates)

    return f"{output_base_dir}/Spielanalyse_{date_string}.mp4"


def build_game_info(segments):
    """Groups segments by game date and determines the title strategy per group.

    Returns a dict: {game_date: {'per_video_titles': bool, 'game_title': str|None}}
      - per_video_titles=True  : every segment in this group has its own title
      - per_video_titles=False : some/none have a title → game_title holds the fallback
    """
    game_groups = OrderedDict()
    for seg in segments:
        game_date = extract_date_from_filename(seg['videoname'])
        game_groups.setdefault(game_date, []).append(seg)

    game_info = {}
    for gdate, segs in game_groups.items():
        titles = [
            s.get('title') for s in segs
            if s.get('title') and isinstance(s.get('title'), str) and s.get('title').strip()
        ]
        if len(titles) == len(segs) and len(segs) > 0:
            game_info[gdate] = {'per_video_titles': True, 'game_title': None}
        elif len(titles) > 0:
            game_info[gdate] = {'per_video_titles': False, 'game_title': titles[0]}
        else:
            game_info[gdate] = {'per_video_titles': False, 'game_title': None}
    return game_info


def resolve_segments_metadata(segments):
    """Resolves title, subtitle, game_number and segment_number_in_game for each segment.

    Returns a list (same order as input) of dicts:
        {'title': str, 'subtitle': str, 'game_number': int, 'segment_number': int}
    """
    game_info = build_game_info(segments)
    result = []
    current_game_number = 1
    last_game_date = None
    last_videoname = None
    segment_number_in_game = 1

    for segment in segments:
        this_game_date = extract_date_from_filename(segment['videoname'])
        this_videoname = segment['videoname']
        if last_game_date is not None and this_game_date != last_game_date:
            current_game_number += 1
            segment_number_in_game = 1
        elif last_videoname is not None and this_videoname != last_videoname:
            segment_number_in_game = 1
        last_game_date = this_game_date
        last_videoname = this_videoname

        ginfo = game_info.get(this_game_date, {'per_video_titles': False, 'game_title': None})
        seg_title = segment.get('title')
        if seg_title and isinstance(seg_title, str) and seg_title.strip():
            title = seg_title
        elif ginfo.get('game_title'):
            title = ginfo['game_title']
        else:
            title = f"Spiel {current_game_number}"

        sub = segment.get('sub_title')
        subtitle = sub if (sub and isinstance(sub, str) and sub.strip()) else f"Segment {segment_number_in_game}"

        result.append({
            'title': title,
            'subtitle': subtitle,
            'game_number': current_game_number,
            'segment_number': segment_number_in_game,
        })
        segment_number_in_game += 1

    return result

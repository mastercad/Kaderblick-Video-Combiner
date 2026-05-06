"""
Tests für src/segment_utils.py

Abgedeckte Funktionen:
  - extract_date_from_filename
  - format_date_ddmmyyyy
  - generate_output_filename
  - build_game_info
  - resolve_segments_metadata
"""

import pytest
from src.segment_utils import (
    extract_date_from_filename,
    format_date_ddmmyyyy,
    generate_output_filename,
    build_game_info,
    resolve_segments_metadata,
)

# ---------------------------------------------------------------------------
# Fixtures: reale Pfade aus segments_26_04_2026_03_05_2026.csv
# ---------------------------------------------------------------------------

GAME1_HZ1 = (
    "/media/andreas/Kaderblick/Spiel-Aufnahmen/Ligaspiele/Sparkassenkreisoberliga/"
    "26.04.2026 SpG SG Wurgwitz | SG 90 Braunsdorf vs. SpG SG Traktor Reinhardtsdorf |"
    " FSV 1924 Bad Schandau | Hohnsteiner SV/DJI Osmo Action 5/processed/"
    "2026-04-26 - SpG Wurgwitz \u200bSG 90 Braunsdorf vs SG Tr. Rhd. FSV 1924 Bd.Sch."
    " Host. SV - 1. Halbzeit.mp4"
)
GAME1_HZ2 = GAME1_HZ1.replace("1. Halbzeit", "2. Halbzeit")

GAME2_HZ1 = (
    "/media/andreas/Kaderblick/Spiel-Aufnahmen/Ligaspiele/Sparkassenkreisoberliga/"
    "03.05.2026 SpG SG Wurgwitz | SG 90 Braunsdorf vs. SSV 1862 Langburkersdorf/"
    "DJI Osmo Action 5/processed/"
    "2026-05-03 - SpG Wurgwitz \u200bSG 90 Braunsdorf vs SSV 1862 Langburkersdorf"
    " - 1. Halbzeit.mp4"
)
GAME2_HZ2 = GAME2_HZ1.replace("1. Halbzeit", "2. Halbzeit")

TITLE_G1_HZ1 = (
    "SpG SG Wurgwitz | SG 90 Braunsdorf vs. SpG SG Traktor Reinhardtsdorf"
    " | FSV 1924 Bad Schandau | Hohnsteiner SV - 1. Halbzeit"
)
TITLE_G1_HZ2 = TITLE_G1_HZ1.replace("1. Halbzeit", "2. Halbzeit")
TITLE_G2_HZ1 = (
    "SpG Wurgwitz \u200bSG 90 Braunsdorf vs SSV 1862 Langburkersdorf - 1. Halbzeit"
)
TITLE_G2_HZ2 = TITLE_G2_HZ1.replace("1. Halbzeit", "2. Halbzeit")


def _seg(videoname, title="", sub_title="", audio=1, start_minute=0.0, length_seconds=60):
    return {
        "videoname": videoname,
        "title": title,
        "sub_title": sub_title,
        "audio": audio,
        "start_minute": start_minute,
        "length_seconds": length_seconds,
    }


# CSV-Segmente exakt wie in der Datei (15 Stück)
CSV_SEGMENTS = [
    # Spiel 1 – 1. Halbzeit (3 Segmente)
    _seg(GAME1_HZ1, title=TITLE_G1_HZ1, start_minute=6.0, length_seconds=360),
    _seg(GAME1_HZ1, start_minute=17.0, length_seconds=300),
    _seg(GAME1_HZ1, start_minute=33.0, length_seconds=420),
    # Spiel 1 – 2. Halbzeit (4 Segmente)
    _seg(GAME1_HZ2, title=TITLE_G1_HZ2, start_minute=3.5, length_seconds=180),
    _seg(GAME1_HZ2, start_minute=12.0, length_seconds=240),
    _seg(GAME1_HZ2, start_minute=22.0, length_seconds=240),
    _seg(GAME1_HZ2, start_minute=31.5, length_seconds=480),
    # Spiel 2 – 1. Halbzeit (4 Segmente)
    _seg(GAME2_HZ1, title=TITLE_G2_HZ1, start_minute=9.5, length_seconds=480),
    _seg(GAME2_HZ1, start_minute=25.5, length_seconds=150),
    _seg(GAME2_HZ1, start_minute=36.0, length_seconds=210),
    _seg(GAME2_HZ1, start_minute=48.0, length_seconds=360),
    # Spiel 2 – 2. Halbzeit (4 Segmente)
    _seg(GAME2_HZ2, title=TITLE_G2_HZ2, start_minute=5.0, length_seconds=180),
    _seg(GAME2_HZ2, start_minute=14.0, length_seconds=240),
    _seg(GAME2_HZ2, start_minute=32.0, length_seconds=360),
    _seg(GAME2_HZ2, start_minute=41.0, length_seconds=480),
]


# ===========================================================================
# extract_date_from_filename
# ===========================================================================

class TestExtractDateFromFilename:

    # --- Eingabetypen -------------------------------------------------------

    def test_none_returns_none(self):
        assert extract_date_from_filename(None) is None

    def test_int_returns_none(self):
        assert extract_date_from_filename(42) is None

    def test_list_returns_none(self):
        assert extract_date_from_filename([]) is None

    def test_empty_string_returns_none(self):
        assert extract_date_from_filename("") is None

    # --- DJI-Rohdateiname (re.search-Muster) --------------------------------

    def test_dji_basename(self):
        assert extract_date_from_filename("DJI_202604261234561.MP4") == "20260426"

    def test_dji_in_full_path(self):
        path = "/media/DCIM/100MEDIA/DJI_20260503093000.MP4"
        assert extract_date_from_filename(path) == "20260503"

    def test_dji_preferred_over_date_prefix(self):
        # Wenn beides vorkommt: DJI-Muster hat Vorrang (steht zuerst im Code)
        path = "2026-04-26_folder/DJI_20260503093000.MP4"
        assert extract_date_from_filename(path) == "20260503"

    # --- Verarbeitete Dateinamen (YYYY-MM-DD Präfix) -------------------------

    def test_processed_basename_only(self):
        assert extract_date_from_filename("2026-04-26 - Spiel.mp4") == "20260426"

    def test_processed_full_path_game1_hz1(self):
        # Der präzise Regressionsfall aus dem Bug-Report
        assert extract_date_from_filename(GAME1_HZ1) == "20260426"

    def test_processed_full_path_game1_hz2(self):
        assert extract_date_from_filename(GAME1_HZ2) == "20260426"

    def test_processed_full_path_game2_hz1(self):
        assert extract_date_from_filename(GAME2_HZ1) == "20260503"

    def test_processed_full_path_game2_hz2(self):
        assert extract_date_from_filename(GAME2_HZ2) == "20260503"

    def test_month_and_day_not_swapped(self):
        # Zweiter Regressionsfall: Monat/Tag dürfen nicht vertauscht sein
        result = extract_date_from_filename("2026-11-03 - Spiel.mp4")
        assert result == "20261103", f"Erwartet 20261103, erhalten {result}"

    def test_date_anywhere_in_path(self):
        path = "/some/dir/2025-12-31/video.mp4"
        assert extract_date_from_filename(path) == "20251231"

    # --- Kein Match ---------------------------------------------------------

    def test_no_date_returns_none(self):
        assert extract_date_from_filename("video_without_date.mp4") is None

    def test_partial_date_returns_none(self):
        # Nur 4 Ziffern – kein vollständiges YYYY-MM-DD
        assert extract_date_from_filename("2026-04.mp4") is None


# ===========================================================================
# format_date_ddmmyyyy
# ===========================================================================

class TestFormatDateDdmmyyyy:

    def test_valid_date(self):
        assert format_date_ddmmyyyy("20260426") == "26_04_2026"

    def test_another_valid_date(self):
        assert format_date_ddmmyyyy("20260503") == "03_05_2026"

    def test_none_returns_none(self):
        assert format_date_ddmmyyyy(None) is None

    def test_empty_string_returns_none(self):
        assert format_date_ddmmyyyy("") is None

    def test_wrong_length_short_returns_none(self):
        assert format_date_ddmmyyyy("2026042") is None

    def test_wrong_length_long_returns_none(self):
        assert format_date_ddmmyyyy("202604260") is None

    def test_year_month_day_positions(self):
        result = format_date_ddmmyyyy("20261103")
        assert result == "03_11_2026"


# ===========================================================================
# generate_output_filename
# ===========================================================================

class TestGenerateOutputFilename:

    def test_empty_segments_returns_default(self):
        assert generate_output_filename([]) == "output/Spielanalyse.mp4"

    def test_segments_without_videoname(self):
        segs = [{"videoname": None}, {"videoname": ""}]
        assert generate_output_filename(segs) == "output/Spielanalyse.mp4"

    def test_single_game_date(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026.mp4"

    def test_two_games_sorted(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME2_HZ1)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026_03_05_2026.mp4"

    def test_duplicate_dates_only_once(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1), _seg(GAME1_HZ2)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026.mp4"

    def test_custom_output_dir(self):
        segs = [_seg(GAME1_HZ1)]
        result = generate_output_filename(segs, output_base_dir="/tmp/out")
        assert result == "/tmp/out/Spielanalyse_26_04_2026.mp4"

    def test_full_csv_two_dates(self):
        result = generate_output_filename(CSV_SEGMENTS)
        assert result == "output/Spielanalyse_26_04_2026_03_05_2026.mp4"

    def test_three_distinct_dates_ascending(self):
        """Drei Spieltage → alle drei DD_MM_YYYY-Blöcke aufsteigend."""
        GAME3_HZ1 = "2025-10-25 - Spiel3 HZ1.mp4"
        GAME4_HZ1 = "2025-11-02 - Spiel4 HZ1.mp4"
        GAME5_HZ1 = "2025-11-09 - Spiel5 HZ1.mp4"
        segs = [_seg(GAME5_HZ1), _seg(GAME4_HZ1), _seg(GAME3_HZ1)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_25_10_2025_02_11_2025_09_11_2025.mp4"

    def test_input_reverse_order_still_sorted_ascending(self):
        """Neueres Datum zuerst im Input → Ausgabe trotzdem mit früherem Datum vorn."""
        segs = [_seg(GAME2_HZ1), _seg(GAME1_HZ1)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026_03_05_2026.mp4"

    def test_dji_raw_filename_extracts_date(self):
        """DJI-Rohaufnahmen (DJI_YYYYMMDDHHMMSS) liefern korrekte Datumsangabe."""
        segs = [_seg("DJI_20260426143015.MP4")]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026.mp4"

    def test_segment_missing_videoname_key_treated_as_no_date(self):
        """Segment ohne 'videoname'-Schlüssel wird übersprungen."""
        segs = [{"title": "Tor"}, _seg(GAME1_HZ1)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_26_04_2026.mp4"

    def test_all_segments_unrecognizable_returns_default(self):
        """Kein Segment hat ein erkennbares Datum → Fallback-Dateiname."""
        segs = [_seg("unbekannte_datei_ohne_datum.mp4")]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse.mp4"

    def test_output_filename_ends_with_mp4(self):
        segs = [_seg(GAME1_HZ1)]
        assert generate_output_filename(segs).endswith(".mp4")

    def test_output_filename_starts_with_spielanalyse(self):
        segs = [_seg(GAME1_HZ1)]
        assert "Spielanalyse_" in generate_output_filename(segs)

    def test_three_spieltage_real_csv_names(self):
        """Entspricht segments_25_10_2025_02_11_2025_09_11_2025.csv"""
        v1 = "2025-10-25 - HZ1.mp4"
        v2 = "2025-11-02 - HZ1.mp4"
        v3 = "2025-11-09 - HZ1.mp4"
        segs = [_seg(v1), _seg(v2), _seg(v3)]
        result = generate_output_filename(segs)
        assert result == "output/Spielanalyse_25_10_2025_02_11_2025_09_11_2025.mp4"


# ===========================================================================
# build_game_info
# ===========================================================================

class TestBuildGameInfo:

    def test_all_segments_have_titles_per_video(self):
        segs = [
            _seg(GAME1_HZ1, title="Titel A"),
            _seg(GAME1_HZ1, title="Titel B"),
        ]
        info = build_game_info(segs)
        assert "20260426" in info
        assert info["20260426"]["per_video_titles"] is True
        assert info["20260426"]["game_title"] is None

    def test_some_segments_have_titles_uses_first(self):
        segs = [
            _seg(GAME1_HZ1, title="Erster Titel"),
            _seg(GAME1_HZ1, title=""),   # kein Titel
            _seg(GAME1_HZ1),              # kein Titel
        ]
        info = build_game_info(segs)
        assert info["20260426"]["per_video_titles"] is False
        assert info["20260426"]["game_title"] == "Erster Titel"

    def test_no_segments_with_titles_game_title_none(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1)]
        info = build_game_info(segs)
        assert info["20260426"]["per_video_titles"] is False
        assert info["20260426"]["game_title"] is None

    def test_two_games_separate_keys(self):
        segs = [
            _seg(GAME1_HZ1, title="Spiel 1"),
            _seg(GAME2_HZ1, title="Spiel 2"),
        ]
        info = build_game_info(segs)
        assert "20260426" in info
        assert "20260503" in info

    def test_title_whitespace_only_treated_as_no_title(self):
        segs = [
            _seg(GAME1_HZ1, title="   "),
            _seg(GAME1_HZ1, title="\t"),
        ]
        info = build_game_info(segs)
        assert info["20260426"]["per_video_titles"] is False
        assert info["20260426"]["game_title"] is None

    def test_csv_segments_two_games(self):
        info = build_game_info(CSV_SEGMENTS)
        assert set(info.keys()) == {"20260426", "20260503"}
        # Beide Spiele haben Segmente mit und ohne Titel → per_video_titles False
        assert info["20260426"]["per_video_titles"] is False
        assert info["20260503"]["per_video_titles"] is False
        # Erster Titel je Spiel wird als Fallback verwendet
        assert info["20260426"]["game_title"] == TITLE_G1_HZ1
        assert info["20260503"]["game_title"] == TITLE_G2_HZ1


# ===========================================================================
# resolve_segments_metadata
# ===========================================================================

class TestResolveSegmentsMetadata:

    def test_length_matches_input(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert len(result) == len(CSV_SEGMENTS)

    # --- game_number --------------------------------------------------------

    def test_game_number_starts_at_1(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert result[0]["game_number"] == 1

    def test_game_number_increments_between_games(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Segmente 0-6 → Spiel 1, Segmente 7-14 → Spiel 2
        assert all(r["game_number"] == 1 for r in result[:7])
        assert all(r["game_number"] == 2 for r in result[7:])

    def test_game_number_single_game_stays_1(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1), _seg(GAME1_HZ2)]
        result = resolve_segments_metadata(segs)
        assert all(r["game_number"] == 1 for r in result)

    # --- segment_number_in_game ---------------------------------------------

    def test_segment_number_starts_at_1_game1(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert result[0]["segment_number"] == 1

    def test_segment_number_counts_within_game1_hz1(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert [r["segment_number"] for r in result[:3]] == [1, 2, 3]

    def test_segment_number_resets_at_hz2_within_game1(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert result[3]["segment_number"] == 1

    def test_segment_number_counts_within_game1_hz2(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert [r["segment_number"] for r in result[3:7]] == [1, 2, 3, 4]

    def test_segment_number_resets_for_game2(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert result[7]["segment_number"] == 1

    def test_segment_number_counts_within_game2_hz2(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        assert [r["segment_number"] for r in result[7:]] == [1, 2, 3, 4, 1, 2, 3, 4]

    def test_segment_number_resets_at_video_change_within_game(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1), _seg(GAME1_HZ2), _seg(GAME1_HZ2)]
        result = resolve_segments_metadata(segs)
        assert [r["segment_number"] for r in result] == [1, 2, 1, 2]

    # --- title --------------------------------------------------------------

    def test_own_title_takes_precedence(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Seg 0: hat eigenen Titel
        assert result[0]["title"] == TITLE_G1_HZ1
        # Seg 3: hat eigenen Titel (2. Halbzeit)
        assert result[3]["title"] == TITLE_G1_HZ2

    def test_segments_without_title_get_game_fallback(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Seg 1, 2 (Spiel 1, kein Titel) → game_title von Spiel 1
        assert result[1]["title"] == TITLE_G1_HZ1
        assert result[2]["title"] == TITLE_G1_HZ1

    def test_game2_fallback_title_is_not_game1_title(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Regressionstests gegen den ursprünglichen Bug:
        # Segmente von Spiel 2 dürfen NICHT den Titel von Spiel 1 bekommen
        for r in result[7:]:
            assert TITLE_G1_HZ1 not in r["title"], (
                f"Segment {r['segment_number']} von Spiel 2 trägt fälschlich den Titel von Spiel 1"
            )

    def test_game2_segments_without_title_get_game2_fallback(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Seg 8, 9, 10 (Spiel 2, kein Titel) → game_title von Spiel 2
        assert result[8]["title"] == TITLE_G2_HZ1
        assert result[9]["title"] == TITLE_G2_HZ1
        assert result[10]["title"] == TITLE_G2_HZ1

    def test_no_title_no_game_title_fallback_to_spielnummer(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1)]
        result = resolve_segments_metadata(segs)
        assert result[0]["title"] == "Spiel 1"
        assert result[1]["title"] == "Spiel 1"

    def test_whitespace_title_treated_as_no_title(self):
        segs = [_seg(GAME1_HZ1, title="  "), _seg(GAME1_HZ1, title="\t")]
        result = resolve_segments_metadata(segs)
        assert result[0]["title"] == "Spiel 1"

    # --- subtitle -----------------------------------------------------------

    def test_own_sub_title_takes_precedence(self):
        segs = [_seg(GAME1_HZ1, sub_title="Mein Untertitel")]
        result = resolve_segments_metadata(segs)
        assert result[0]["subtitle"] == "Mein Untertitel"

    def test_subtitle_fallback_is_segment_number(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1)]
        result = resolve_segments_metadata(segs)
        assert result[0]["subtitle"] == "Segment 1"
        assert result[1]["subtitle"] == "Segment 2"

    def test_subtitle_resets_after_game_change(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME2_HZ1)]
        result = resolve_segments_metadata(segs)
        assert result[0]["subtitle"] == "Segment 1"
        assert result[1]["subtitle"] == "Segment 1"  # Neues Spiel → reset

    def test_subtitle_resets_at_video_change_within_game(self):
        segs = [_seg(GAME1_HZ1), _seg(GAME1_HZ1), _seg(GAME1_HZ2)]
        result = resolve_segments_metadata(segs)
        assert [r["subtitle"] for r in result] == ["Segment 1", "Segment 2", "Segment 1"]

    def test_whitespace_subtitle_treated_as_no_subtitle(self):
        segs = [_seg(GAME1_HZ1, sub_title="   ")]
        result = resolve_segments_metadata(segs)
        assert result[0]["subtitle"] == "Segment 1"

    # --- Vollständige Regression gegen CSV-Daten ----------------------------

    def test_csv_all_game_numbers(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        expected_game_numbers = [1] * 7 + [2] * 8
        assert [r["game_number"] for r in result] == expected_game_numbers

    def test_csv_all_segment_numbers(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Resets per video: HZ1 (3), HZ2 (4), HZ1 (4), HZ2 (4)
        expected = [1, 2, 3,  1, 2, 3, 4,  1, 2, 3, 4,  1, 2, 3, 4]
        assert [r["segment_number"] for r in result] == expected

    def test_csv_all_titles(self):
        result = resolve_segments_metadata(CSV_SEGMENTS)
        # Segmente 0-2: Spiel 1, 1. HZ
        assert result[0]["title"] == TITLE_G1_HZ1
        assert result[1]["title"] == TITLE_G1_HZ1
        assert result[2]["title"] == TITLE_G1_HZ1
        # Segmente 3-6: Spiel 1, 2. HZ hat eigenen Titel; 4-6 → game_title
        assert result[3]["title"] == TITLE_G1_HZ2
        assert result[4]["title"] == TITLE_G1_HZ1   # game_title = erster Titel des Spiels
        assert result[5]["title"] == TITLE_G1_HZ1
        assert result[6]["title"] == TITLE_G1_HZ1
        # Segmente 7-10: Spiel 2, 1. HZ
        assert result[7]["title"] == TITLE_G2_HZ1
        assert result[8]["title"] == TITLE_G2_HZ1
        assert result[9]["title"] == TITLE_G2_HZ1
        assert result[10]["title"] == TITLE_G2_HZ1
        # Segmente 11-14: Spiel 2, 2. HZ hat eigenen Titel; 12-14 → game_title
        assert result[11]["title"] == TITLE_G2_HZ2
        assert result[12]["title"] == TITLE_G2_HZ1  # game_title = erster Titel des Spiels
        assert result[13]["title"] == TITLE_G2_HZ1
        assert result[14]["title"] == TITLE_G2_HZ1

"""
Tests für compute_move_up / compute_move_down aus src/gui/main_window.py

Getestete Szenarien:
  compute_move_up:
    - leere Auswahl → kein Move
    - Zeile 0 selektiert → kein Move (würde über Listenrand gehen)
    - Zeile 0 in Multi-Selektion → kein Move
    - einzelne Zeile in der Mitte
    - einzelne unterste Zeile
    - zusammenhängende Block-Auswahl
    - nicht-zusammenhängende Auswahl (Lücken)
    - alle Zeilen selektiert → kein Move
    - Duplikate in selected_rows werden ignoriert
    - neue Auswahl stimmt nach dem Move

  compute_move_down:
    - leere Auswahl → kein Move
    - letzte Zeile selektiert → kein Move
    - letzte Zeile in Multi-Selektion → kein Move
    - einzelne Zeile in der Mitte
    - einzelne oberste Zeile
    - zusammenhängende Block-Auswahl
    - nicht-zusammenhängende Auswahl (Lücken)
    - alle Zeilen selektiert → kein Move
    - Duplikate in selected_rows werden ignoriert
    - neue Auswahl stimmt nach dem Move

  Integrations-ähnliche Szenarien:
    - mehrfach hintereinander nach oben schieben
    - mehrfach hintereinander nach unten schieben
    - Lücken-Auswahl nach oben bis ans Ende schieben
    - Lücken-Auswahl nach unten bis ans Ende schieben
    - Originalinhalt bleibt erhalten (keine Duplikate/Verluste)
    - Eingabeliste wird nicht mutiert
"""

import pytest
from src.gui.main_window import compute_move_up, compute_move_down


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _segs(labels):
    """Erzeugt eine Liste minimaler Segment-Dicts mit 'title' als Bezeichner."""
    return [{"title": lbl, "videoname": f"v{i}.mp4"} for i, lbl in enumerate(labels)]


def _titles(segs):
    return [s["title"] for s in segs]


# ---------------------------------------------------------------------------
# compute_move_up – Kein-Move-Fälle
# ---------------------------------------------------------------------------

class TestComputeMoveUpNoOp:

    def test_empty_selection_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, new_rows = compute_move_up(segs, [])
        assert new_segs is segs

    def test_empty_selection_returns_empty_rows(self):
        segs = _segs(["A", "B", "C"])
        _, new_rows = compute_move_up(segs, [])
        assert new_rows == []

    def test_row0_selected_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, _ = compute_move_up(segs, [0])
        assert new_segs is segs

    def test_row0_in_multi_selection_returns_same_object(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, _ = compute_move_up(segs, [0, 2])
        assert new_segs is segs

    def test_all_rows_selected_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, _ = compute_move_up(segs, [0, 1, 2])
        assert new_segs is segs

    def test_single_element_list_row0_returns_same_object(self):
        segs = _segs(["A"])
        new_segs, _ = compute_move_up(segs, [0])
        assert new_segs is segs


# ---------------------------------------------------------------------------
# compute_move_up – Bewegungen
# ---------------------------------------------------------------------------

class TestComputeMoveUpMove:

    def test_single_row_middle(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_up(segs, [2])
        assert _titles(new_segs) == ["A", "C", "B", "D"]
        assert new_rows == [1]

    def test_single_row_last(self):
        segs = _segs(["A", "B", "C"])
        new_segs, new_rows = compute_move_up(segs, [2])
        assert _titles(new_segs) == ["A", "C", "B"]
        assert new_rows == [1]

    def test_single_row_second(self):
        segs = _segs(["A", "B", "C"])
        new_segs, new_rows = compute_move_up(segs, [1])
        assert _titles(new_segs) == ["B", "A", "C"]
        assert new_rows == [0]

    def test_contiguous_block_not_at_top(self):
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, new_rows = compute_move_up(segs, [2, 3, 4])
        assert _titles(new_segs) == ["A", "C", "D", "E", "B"]
        assert new_rows == [1, 2, 3]

    def test_contiguous_block_at_position_1(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_up(segs, [1, 2])
        assert _titles(new_segs) == ["B", "C", "A", "D"]
        assert new_rows == [0, 1]

    def test_non_contiguous_no_row0(self):
        # Lücken: Zeilen 1 und 3 aus [A, B, C, D, E]
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, new_rows = compute_move_up(segs, [1, 3])
        # Row 1 → 0, Row 3 → 2
        assert _titles(new_segs) == ["B", "A", "D", "C", "E"]
        assert new_rows == [0, 2]

    def test_non_contiguous_gap_in_middle(self):
        # [A, B, C, D, E, F] → Zeilen 2 und 5 hoch
        segs = _segs(["A", "B", "C", "D", "E", "F"])
        new_segs, new_rows = compute_move_up(segs, [2, 5])
        assert _titles(new_segs) == ["A", "C", "B", "D", "F", "E"]
        assert new_rows == [1, 4]

    def test_unsorted_input_rows_handled(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_up(segs, [3, 1])  # absichtlich ungeordnet
        assert _titles(new_segs) == ["B", "A", "D", "C"]
        assert sorted(new_rows) == [0, 2]

    def test_duplicate_rows_in_input_ignored(self):
        segs = _segs(["A", "B", "C"])
        new_segs1, _ = compute_move_up(segs, [2])
        new_segs2, _ = compute_move_up(segs, [2, 2, 2])
        assert _titles(new_segs1) == _titles(new_segs2)

    def test_input_list_not_mutated(self):
        segs = _segs(["A", "B", "C"])
        original_titles = _titles(segs)
        compute_move_up(segs, [2])
        assert _titles(segs) == original_titles

    def test_no_elements_lost_or_duplicated(self):
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, _ = compute_move_up(segs, [1, 3])
        assert sorted(_titles(new_segs)) == ["A", "B", "C", "D", "E"]
        assert len(new_segs) == 5

    def test_two_row_list_move_last_up(self):
        segs = _segs(["A", "B"])
        new_segs, new_rows = compute_move_up(segs, [1])
        assert _titles(new_segs) == ["B", "A"]
        assert new_rows == [0]


# ---------------------------------------------------------------------------
# compute_move_down – Kein-Move-Fälle
# ---------------------------------------------------------------------------

class TestComputeMoveDownNoOp:

    def test_empty_selection_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, _ = compute_move_down(segs, [])
        assert new_segs is segs

    def test_empty_selection_returns_empty_rows(self):
        segs = _segs(["A", "B", "C"])
        _, new_rows = compute_move_down(segs, [])
        assert new_rows == []

    def test_last_row_selected_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, _ = compute_move_down(segs, [2])
        assert new_segs is segs

    def test_last_row_in_multi_selection_returns_same_object(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, _ = compute_move_down(segs, [1, 3])
        assert new_segs is segs

    def test_all_rows_selected_returns_same_object(self):
        segs = _segs(["A", "B", "C"])
        new_segs, _ = compute_move_down(segs, [0, 1, 2])
        assert new_segs is segs

    def test_single_element_list_row0_returns_same_object(self):
        segs = _segs(["A"])
        new_segs, _ = compute_move_down(segs, [0])
        assert new_segs is segs


# ---------------------------------------------------------------------------
# compute_move_down – Bewegungen
# ---------------------------------------------------------------------------

class TestComputeMoveDownMove:

    def test_single_row_middle(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_down(segs, [1])
        assert _titles(new_segs) == ["A", "C", "B", "D"]
        assert new_rows == [2]

    def test_single_row_first(self):
        segs = _segs(["A", "B", "C"])
        new_segs, new_rows = compute_move_down(segs, [0])
        assert _titles(new_segs) == ["B", "A", "C"]
        assert new_rows == [1]

    def test_single_row_second_to_last(self):
        segs = _segs(["A", "B", "C"])
        new_segs, new_rows = compute_move_down(segs, [1])
        assert _titles(new_segs) == ["A", "C", "B"]
        assert new_rows == [2]

    def test_contiguous_block_not_at_bottom(self):
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, new_rows = compute_move_down(segs, [0, 1, 2])
        assert _titles(new_segs) == ["D", "A", "B", "C", "E"]
        assert new_rows == [1, 2, 3]

    def test_contiguous_block_at_second_to_last(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_down(segs, [1, 2])
        assert _titles(new_segs) == ["A", "D", "B", "C"]
        assert new_rows == [2, 3]

    def test_non_contiguous_no_last_row(self):
        # Zeilen 0 und 2 aus [A, B, C, D, E]
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, new_rows = compute_move_down(segs, [0, 2])
        # Row 0 → 1, Row 2 → 3
        assert _titles(new_segs) == ["B", "A", "D", "C", "E"]
        assert new_rows == [1, 3]

    def test_non_contiguous_gap_in_middle(self):
        # [A, B, C, D, E, F] → Zeilen 0 und 3 runter
        segs = _segs(["A", "B", "C", "D", "E", "F"])
        new_segs, new_rows = compute_move_down(segs, [0, 3])
        assert _titles(new_segs) == ["B", "A", "C", "E", "D", "F"]
        assert new_rows == [1, 4]

    def test_unsorted_input_rows_handled(self):
        segs = _segs(["A", "B", "C", "D"])
        new_segs, new_rows = compute_move_down(segs, [2, 0])  # absichtlich ungeordnet
        assert _titles(new_segs) == ["B", "A", "D", "C"]
        assert sorted(new_rows) == [1, 3]

    def test_duplicate_rows_in_input_ignored(self):
        segs = _segs(["A", "B", "C"])
        new_segs1, _ = compute_move_down(segs, [0])
        new_segs2, _ = compute_move_down(segs, [0, 0, 0])
        assert _titles(new_segs1) == _titles(new_segs2)

    def test_input_list_not_mutated(self):
        segs = _segs(["A", "B", "C"])
        original_titles = _titles(segs)
        compute_move_down(segs, [0])
        assert _titles(segs) == original_titles

    def test_no_elements_lost_or_duplicated(self):
        segs = _segs(["A", "B", "C", "D", "E"])
        new_segs, _ = compute_move_down(segs, [0, 2])
        assert sorted(_titles(new_segs)) == ["A", "B", "C", "D", "E"]
        assert len(new_segs) == 5

    def test_two_row_list_move_first_down(self):
        segs = _segs(["A", "B"])
        new_segs, new_rows = compute_move_down(segs, [0])
        assert _titles(new_segs) == ["B", "A"]
        assert new_rows == [1]


# ---------------------------------------------------------------------------
# Integrations-ähnliche Szenarien: wiederholte Moves
# ---------------------------------------------------------------------------

class TestRepeatedMoves:

    def test_move_up_repeatedly_until_top(self):
        segs = _segs(["A", "B", "C", "D"])
        # "D" (Zeile 3) schrittweise nach oben
        rows = [3]
        for expected_pos in [2, 1, 0]:
            segs, rows = compute_move_up(segs, rows)
            assert rows == [expected_pos]
            assert segs[expected_pos]["title"] == "D"
        # Nächster Versuch: kein Move mehr möglich
        new_segs, _ = compute_move_up(segs, rows)
        assert new_segs is segs

    def test_move_down_repeatedly_until_bottom(self):
        segs = _segs(["A", "B", "C", "D"])
        # "A" (Zeile 0) schrittweise nach unten
        rows = [0]
        for expected_pos in [1, 2, 3]:
            segs, rows = compute_move_down(segs, rows)
            assert rows == [expected_pos]
            assert segs[expected_pos]["title"] == "A"
        # Nächster Versuch: kein Move mehr möglich
        new_segs, _ = compute_move_down(segs, rows)
        assert new_segs is segs

    def test_gapped_selection_move_up_to_top(self):
        # [A, B, C, D, E] → Zeilen 2 und 4 hoch, bis Zeile 2 oben ist
        segs = _segs(["A", "B", "C", "D", "E"])
        rows = [2, 4]
        segs, rows = compute_move_up(segs, rows)
        assert _titles(segs) == ["A", "C", "B", "E", "D"]
        assert rows == [1, 3]
        segs, rows = compute_move_up(segs, rows)
        assert _titles(segs) == ["C", "A", "E", "B", "D"]
        assert rows == [0, 2]
        # Jetzt ist Zeile 0 in der Auswahl → kein Move mehr
        new_segs, _ = compute_move_up(segs, rows)
        assert new_segs is segs

    def test_gapped_selection_move_down_to_bottom(self):
        # [A, B, C, D, E] → Zeilen 0 und 2 runter, bis Zeile 2 unten ist
        segs = _segs(["A", "B", "C", "D", "E"])
        rows = [0, 2]
        segs, rows = compute_move_down(segs, rows)
        assert _titles(segs) == ["B", "A", "D", "C", "E"]
        assert rows == [1, 3]
        segs, rows = compute_move_down(segs, rows)
        assert _titles(segs) == ["B", "D", "A", "E", "C"]
        assert rows == [2, 4]
        # Letzte Zeile (4) in Auswahl → kein Move mehr
        new_segs, _ = compute_move_down(segs, rows)
        assert new_segs is segs

    def test_move_up_then_down_roundtrip(self):
        original = _segs(["A", "B", "C", "D", "E"])
        segs = list(original)
        rows = [1, 3]
        # 1× hoch
        segs, rows = compute_move_up(segs, rows)
        # 1× runter (zurück)
        segs, rows = compute_move_down(segs, rows)
        assert _titles(segs) == _titles(original)

    def test_move_down_then_up_roundtrip(self):
        original = _segs(["A", "B", "C", "D", "E"])
        segs = list(original)
        rows = [0, 2]
        # 1× runter
        segs, rows = compute_move_down(segs, rows)
        # 1× hoch (zurück)
        segs, rows = compute_move_up(segs, rows)
        assert _titles(segs) == _titles(original)

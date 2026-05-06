"""
Tests für die Abbruch-Funktionalität der Video-Pipeline.

Getestete Szenarien:
  cancel_pipeline():
    - Setzt _cancel_requested = True
    - Kann mehrfach aufgerufen werden ohne Fehler

  PipelineCancelledError:
    - Ist eine Unterklasse von Exception
    - Kann geraist und gefangen werden
    - Enthält die Fehlermeldung

  analyze_video_resolutions():
    - Bricht beim ersten Segment ab wenn Flag vor dem Aufruf gesetzt
    - Bricht beim zweiten Segment ab wenn Flag mid-loop gesetzt wird
    - Läuft normal durch wenn Flag nicht gesetzt

  assemble_ffmpeg_script():
    - Setzt _cancel_requested am Anfang auf False zurück (stale cancel wird gelöscht)
    - Raises PipelineCancelledError nach Phase 1 wenn Flag in Phase-1-Progress gesetzt
    - Raises PipelineCancelledError vor Phase 3 wenn Flag in Phase-2-Progress gesetzt
    - Raises PipelineCancelledError im Executor-Loop wenn Flag nach Future-Result gesetzt

  run_video_pipeline():
    - Gibt {'success': False, 'cancelled': True, 'error': None} zurück wenn abgebrochen
    - Startet keinen YouTube-Upload nach Abbruch
"""

import pytest
from unittest.mock import MagicMock, patch

import src.processing as proc_mod
from src.processing import PipelineCancelledError, cancel_pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_cancel_flag():
    """Stellt sicher, dass das Cancel-Flag vor und nach jedem Test False ist."""
    proc_mod._cancel_requested = False
    yield
    proc_mod._cancel_requested = False


def _fake_segment(tmp_path, name="video.mp4"):
    f = tmp_path / name
    f.touch()
    return f


def _seg_dict(videoname, start_minute=0.0, length_seconds=60):
    return {'videoname': str(videoname), 'start_minute': start_minute,
            'length_seconds': length_seconds, 'audio': 1}


def _mock_assemble_deps(monkeypatch):
    """Patcht alle schweren Abhängigkeiten in assemble_ffmpeg_script weg."""
    monkeypatch.setattr('src.processing.detect_hw_encoder', lambda: 'libx264')
    monkeypatch.setattr('src.processing.create_textclip', lambda *a, **kw: None)
    monkeypatch.setattr('src.processing.retrieve_video_duration', lambda p: 300.0)
    monkeypatch.setattr('src.processing.is_video_file_complete', lambda f, **kw: False)
    monkeypatch.setattr(
        'src.processing.resolve_segments_metadata',
        lambda segs: [
            {'title': 'T', 'subtitle': 'S', 'game_number': 1, 'segment_number': i + 1}
            for i, _ in enumerate(segs)
        ]
    )


# ---------------------------------------------------------------------------
# cancel_pipeline()
# ---------------------------------------------------------------------------

class TestCancelPipelineFunction:

    def test_sets_cancel_flag(self):
        assert proc_mod._cancel_requested is False
        cancel_pipeline()
        assert proc_mod._cancel_requested is True

    def test_idempotent(self):
        cancel_pipeline()
        cancel_pipeline()
        assert proc_mod._cancel_requested is True

    def test_does_not_raise_without_active_process(self):
        """Aufruf ohne laufenden ffmpeg-Prozess darf keinen Fehler verursachen."""
        proc_mod._concat_proc = None
        cancel_pipeline()  # should not raise


# ---------------------------------------------------------------------------
# PipelineCancelledError
# ---------------------------------------------------------------------------

class TestPipelineCancelledError:

    def test_is_subclass_of_exception(self):
        assert issubclass(PipelineCancelledError, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PipelineCancelledError):
            raise PipelineCancelledError("Abgebrochen")

    def test_message_is_preserved(self):
        with pytest.raises(PipelineCancelledError, match="Abgebrochen"):
            raise PipelineCancelledError("Abgebrochen")

    def test_is_catchable_as_exception(self):
        caught = None
        try:
            raise PipelineCancelledError("test")
        except Exception as e:
            caught = e
        assert isinstance(caught, PipelineCancelledError)


# ---------------------------------------------------------------------------
# analyze_video_resolutions() – Cancel-Verhalten
# ---------------------------------------------------------------------------

class TestAnalyzeVideoResolutionsCancelled:

    def test_raises_immediately_when_flag_set_before_call(self, tmp_path):
        """Flag bereits gesetzt → erster Loop-Schritt bricht sofort ab."""
        fake = _fake_segment(tmp_path)
        proc_mod._cancel_requested = True

        with pytest.raises(PipelineCancelledError):
            proc_mod.analyze_video_resolutions([_seg_dict(fake)], '/')

    def test_raises_on_second_segment_when_flag_set_after_first(self, tmp_path, monkeypatch):
        """Flag wird nach Analyse des ersten Segments gesetzt → zweites bricht ab."""
        fake = _fake_segment(tmp_path)
        segments = [_seg_dict(fake), _seg_dict(fake)]

        call_count = 0
        def fake_specs(_path):
            nonlocal call_count
            call_count += 1
            proc_mod._cancel_requested = True  # nach erstem Aufruf setzen
            return {'width': 1920, 'height': 1080, 'fps': 25,
                    'codec': 'h264', 'pix_fmt': 'yuv420p', 'fps_raw': '25'}

        monkeypatch.setattr('src.processing.extract_video_specs', fake_specs)

        with pytest.raises(PipelineCancelledError):
            proc_mod.analyze_video_resolutions(segments, '/')

        # Nur der erste Aufruf wurde abgeschlossen, dann abgebrochen
        assert call_count == 1

    def test_completes_normally_when_flag_not_set(self, tmp_path, monkeypatch):
        fake = _fake_segment(tmp_path)
        monkeypatch.setattr('src.processing.extract_video_specs', lambda _: {
            'width': 1920, 'height': 1080, 'fps': 25,
            'codec': 'h264', 'pix_fmt': 'yuv420p', 'fps_raw': '25'
        })

        result = proc_mod.analyze_video_resolutions([_seg_dict(fake)], '/')
        assert result[0] == 1920  # target_width


# ---------------------------------------------------------------------------
# assemble_ffmpeg_script() – Cancel-Verhalten
# ---------------------------------------------------------------------------

class TestAssembleFfmpegScriptCancelled:

    def test_resets_stale_cancel_flag_at_start(self, tmp_path, monkeypatch):
        """assemble_ffmpeg_script setzt _cancel_requested = False am Anfang zurück.

        Damit ein Abbruch aus einem vorherigen Lauf nicht die nächste Pipeline blockiert.
        """
        proc_mod._cancel_requested = True  # stale cancel

        captured = []

        def capture_first_progress(current, total, label):
            if not captured:
                captured.append(proc_mod._cancel_requested)

        _mock_assemble_deps(monkeypatch)
        # Leere Segmentliste + merge_videos=False → schnellster Pfad, kein ffmpeg
        proc_mod.assemble_ffmpeg_script(
            [], '/', tmp_path / 'out.mp4',
            progress_callback=capture_first_progress,
            merge_videos=False,
        )

        assert captured, "progress_callback wurde nie aufgerufen"
        assert captured[0] is False, "Flag muss nach dem Reset False sein"

    def test_raises_after_phase1_when_flag_set_in_progress(self, tmp_path, monkeypatch):
        """Flag wird im Phase-1-Progress-Callback gesetzt → raise nach der Schleife."""
        fake = _fake_segment(tmp_path)

        def cancel_on_phase1(current, total, label):
            if 'Phase 1: Segment' in label:
                proc_mod._cancel_requested = True

        _mock_assemble_deps(monkeypatch)
        with pytest.raises(PipelineCancelledError):
            proc_mod.assemble_ffmpeg_script(
                [_seg_dict(fake)], '/', tmp_path / 'out.mp4',
                progress_callback=cancel_on_phase1,
                chapter_transitions=False,
            )

    def test_raises_before_phase3_when_flag_set_in_phase2_progress(self, tmp_path, monkeypatch):
        """Flag wird im Phase-2-Progress-Callback gesetzt → raise vor Phase 3."""

        def cancel_on_phase2(current, total, label):
            if 'Phase 2' in label:
                proc_mod._cancel_requested = True

        _mock_assemble_deps(monkeypatch)
        # Leere Segmentliste → Phase-2-Progress wird einmalig aufgerufen, kein Executor
        with pytest.raises(PipelineCancelledError):
            proc_mod.assemble_ffmpeg_script(
                [], '/', tmp_path / 'out.mp4',
                progress_callback=cancel_on_phase2,
                merge_videos=True,
            )

    def test_raises_in_executor_loop_when_flag_set_after_future_result(self, tmp_path, monkeypatch):
        """Flag wird nach dem ersten Future-Result gesetzt → raise im Executor-Loop."""
        fake = _fake_segment(tmp_path)

        _mock_assemble_deps(monkeypatch)

        # Mock-Future der ein Erfolg-Ergebnis liefert und dabei das Flag setzt
        mock_future = MagicMock()
        def set_flag_and_succeed():
            proc_mod._cancel_requested = True
            return (str(fake), 0.1, True, None, False)
        mock_future.result.side_effect = set_flag_and_succeed

        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit.return_value = mock_future

        with patch('src.processing.ProcessPoolExecutor', return_value=mock_executor), \
             patch('src.processing.as_completed', return_value=[mock_future]):
            with pytest.raises(PipelineCancelledError):
                proc_mod.assemble_ffmpeg_script(
                    [_seg_dict(fake)], '/', tmp_path / 'out.mp4',
                    chapter_transitions=False,
                    merge_videos=True,
                )


# ---------------------------------------------------------------------------
# run_video_pipeline() – Cancel-Verhalten
# ---------------------------------------------------------------------------

class TestRunVideoPipelineCancelled:

    def _mock_analyze_raises(self, monkeypatch):
        def raise_cancelled(*a, **kw):
            raise PipelineCancelledError("Abgebrochen")
        monkeypatch.setattr('src.processing.analyze_video_resolutions', raise_cancelled)

    def test_returns_cancelled_true(self, monkeypatch):
        from src.main_utils import run_video_pipeline
        self._mock_analyze_raises(monkeypatch)

        result = run_video_pipeline([_seg_dict('/fake/v.mp4')], {})

        assert result['success'] is False
        assert result['cancelled'] is True

    def test_error_is_none_on_cancel(self, monkeypatch):
        from src.main_utils import run_video_pipeline
        self._mock_analyze_raises(monkeypatch)

        result = run_video_pipeline([_seg_dict('/fake/v.mp4')], {})

        assert result['error'] is None

    def test_video_id_is_none_on_cancel(self, monkeypatch):
        from src.main_utils import run_video_pipeline
        self._mock_analyze_raises(monkeypatch)

        result = run_video_pipeline([_seg_dict('/fake/v.mp4')], {})

        assert result['video_id'] is None

    def test_no_youtube_upload_after_cancel(self, monkeypatch):
        """Nach Abbruch darf kein YouTube-Upload gestartet werden."""
        from src.main_utils import run_video_pipeline
        self._mock_analyze_raises(monkeypatch)

        upload_called = []
        monkeypatch.setattr(
            'src.youtube_upload.upload_to_youtube',
            lambda *a, **kw: upload_called.append(True) or 'fake_id'
        )

        result = run_video_pipeline(
            [_seg_dict('/fake/v.mp4')],
            {'youtube_upload': True, 'merge_videos': True}
        )

        assert result['cancelled'] is True
        assert upload_called == [], "YouTube-Upload darf nach Abbruch nicht aufgerufen werden"

    def test_normal_pipeline_error_has_cancelled_false(self, monkeypatch):
        """Ein normaler Fehler (nicht Abbruch) liefert cancelled=False."""
        from src.main_utils import run_video_pipeline

        def raise_runtime(*a, **kw):
            raise RuntimeError("ffmpeg crash")
        monkeypatch.setattr('src.processing.analyze_video_resolutions', raise_runtime)

        result = run_video_pipeline([_seg_dict('/fake/v.mp4')], {})

        assert result['success'] is False
        assert result.get('cancelled', False) is False
        assert 'ffmpeg crash' in (result['error'] or '')

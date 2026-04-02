"""
KADERBLICK Video Combiner GUI – Package

Modulstruktur:
    src/gui/dialogs.py      – TimeRangeDialog, YouTubeOptionsDialog
    src/gui/worker.py       – PipelineWorker (QThread)
    src/gui/main_window.py  – VideoSegmentGUI (QMainWindow)
"""

import sys
from PyQt5.QtWidgets import QApplication

from shared.kaderblick_qt_theme import apply_application_theme
from src.gui.main_window import VideoSegmentGUI


def main():
    """Startet die GUI-Anwendung."""
    app = QApplication(sys.argv)
    apply_application_theme(app)
    win = VideoSegmentGUI()
    win.show()
    sys.exit(app.exec_())

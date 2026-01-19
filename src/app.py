from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.styles import apply_style


class App(QApplication):
    def __init__(self, sys_argv: list[str]) -> None:
        super().__init__(sys_argv)
        self.translator = QTranslator()
        self.main_window = MainWindow()
        self._wire_events()

    def load_language(self, lang_code: str | None = None) -> None:
        """Load a translation file for the given language code (e.g., 'ar', 'fr')."""
        self.removeTranslator(self.translator)
        if lang_code:
            translation_file = f"app_{lang_code}.qm"
            path = Path(__file__).parent / "translations" / translation_file
            if self.translator.load(str(path)):
                self.installTranslator(self.translator)

    def _wire_events(self) -> None:
        self.main_window.training_page.lang_combo.currentTextChanged.connect(
            self._on_language_changed
        )

    def _on_language_changed(self, lang_name: str) -> None:
        if lang_name == "English":
            self.load_language()  # Unload translator
        elif lang_name == "العربية":
            self.load_language("ar")
        elif lang_name == "Français":
            self.load_language("fr")


def run() -> None:
    app = App(sys.argv)
    apply_style(app)

    app.main_window.show()

    sys.exit(app.exec())

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.widgets.soroban_view import SorobanView

TUTORIAL_STEPS = [
    {
        "text": "Welcome! This is the Soroban (Japanese abacus). It is used for arithmetic. Let's learn how to read it.\nThis is the number 0. All beads are away from the central beam.",
        "value": 0,
    },
    {
        "text": 'Each bead in the lower section is worth 1. It is counted by moving it up toward the beam.\nThis is the number 1.',
        "value": 1,
    },
    {
        "text": "Let's make the number 3. Move three lower beads up.",
        "value": 3,
    },
    {
        "text": 'To make the number 4, move four lower beads up.',
        "value": 4,
    },
    {
        "text": 'The bead in the upper section is worth 5. To show 5, move the upper bead down toward the beam and move all lower beads away.',
        "value": 5,
    },
    {
        "text": 'To make 6, use the upper bead (5) and one lower bead (1).\nSo, 5 + 1 = 6.',
        "value": 6,
    },
    {
        "text": 'This is the number 8. It is made from the upper bead (5) and three lower beads (3).\nSo, 5 + 3 = 8.',
        "value": 8,
    },
    {
        "text": "What about larger numbers? Each column represents a new place value (ones, tens, hundreds).\nThis is the number 10. '1' is in the tens place and '0' is in the ones place.",
        "value": 10,
    },
    {
        "text": "Let's try 27. That means '2' in the tens place and '7' in the ones place.",
        "value": 27,
    },
    {
        "text": 'This is the number 51.',
        "value": 51,
    },
    {
        "text": 'Finally, the number 123.',
        "value": 123,
    },
    {
        "text": 'You have learned the basics! Try moving the beads yourself.\nAfter that, go to the Training page to practice.',
        "value": 0,
    },
]


class LearnPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._current_step = 0

        root_layout = QHBoxLayout(self)
        root_layout.setAlignment(Qt.AlignCenter)
        root_layout.setSpacing(20)

        # Left side (Soroban)
        self._soroban = SorobanView(columns=4)
        root_layout.addWidget(self._soroban)

        # Right side (Instructions and Navigation)
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setAlignment(Qt.AlignCenter)

        self._instruction_label = QLabel()
        self._instruction_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(14)
        self._instruction_label.setFont(font)
        self._instruction_label.setMinimumWidth(350)
        right_panel_layout.addWidget(self._instruction_label)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        nav_layout.setAlignment(Qt.AlignCenter)

        self._prev_button = QPushButton()
        self._prev_button.clicked.connect(self._go_prev)
        nav_layout.addWidget(self._prev_button)

        self._next_button = QPushButton()
        self._next_button.clicked.connect(self._go_next)
        nav_layout.addWidget(self._next_button)

        right_panel_layout.addLayout(nav_layout)
        root_layout.addLayout(right_panel_layout)

        self.retranslate_ui()

    def changeEvent(self, event) -> None:
        if event.type() == event.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def _is_rtl_language(self) -> bool:
        sample = self.tr("Previous")
        return any("؀" <= ch <= "ۿ" for ch in sample)

    def _apply_language_layout(self) -> None:
        is_rtl = self._is_rtl_language()
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        alignment = Qt.AlignRight if is_rtl else Qt.AlignLeft
        self.setLayoutDirection(direction)
        self._instruction_label.setAlignment(alignment | Qt.AlignVCenter)

    def retranslate_ui(self) -> None:
        self._prev_button.setText(self.tr("Previous"))
        self._next_button.setText(self.tr("Next"))
        self._apply_language_layout()
        self._update_step()

    def _update_step(self) -> None:
        step_data = TUTORIAL_STEPS[self._current_step]

        self._instruction_label.setText(self.tr(step_data["text"]))
        self._soroban.set_value(step_data["value"])

        self._prev_button.setEnabled(self._current_step > 0)
        self._next_button.setEnabled(self._current_step < len(TUTORIAL_STEPS) - 1)

    def _go_next(self) -> None:
        if self._current_step < len(TUTORIAL_STEPS) - 1:
            self._current_step += 1
            self._update_step()

    def _go_prev(self) -> None:
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()

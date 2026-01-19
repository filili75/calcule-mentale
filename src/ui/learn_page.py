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
        "text": "أهلاً بك! هذا هو السوروبان (المعداد الياباني). يُستخدم للقيام بالعمليات الحسابية. لنتعلم كيفية قراءته.\nهذا هو الرقم 0. كل الخرزات بعيدة عن الشريط المركزي.",
        "value": 0,
    },
    {
        "text": "كل خرزة في القسم السفلي تساوي 1. يتم حسابها عن طريق تحريكها للأعلى باتجاه الشريط.\nهذا هو الرقم 1.",
        "value": 1,
    },
    {
        "text": "لنقم بعد الرقم 3. نحرك ثلاث خرزات سفلية للأعلى.",
        "value": 3,
    },
    {
        "text": "لتكوين الرقم 4, نحرك أربع خرزات سفلية للأعلى.",
        "value": 4,
    },
    {
        "text": "الخرزة في القسم العلوي تساوي 5. لإظهار الرقم 5, حرك الخرزة العلوية للأسفل باتجاه الشريط وأبعد كل الخرزات السفلية.",
        "value": 5,
    },
    {
        "text": "لتكوين الرقم 6, نستخدم الخرزة العلوية (5) وخرزة سفلية واحدة (1).\nإذًا, 5 + 1 = 6.",
        "value": 6,
    },
    {
        "text": "هذا هو الرقم 8. وهو مكون من الخرزة العلوية (5) وثلاث خرزات سفلية (3).\nإذًا, 5 + 3 = 8.",
        "value": 8,
    },
    {
        "text": "ماذا عن الأرقام الأكبر؟ كل عمود يمثل خانة جديدة (آحاد, عشرات, مئات).\nهذا هو الرقم 10. '1' في خانة العشرات و '0' في خانة الآحاد.",
        "value": 10,
    },
    {
        "text": "لنجرب الرقم 27. هذا يعني '2' في خانة العشرات و '7' في خانة الآحاد.",
        "value": 27,
    },
    {
        "text": "هذا هو الرقم 51.",
        "value": 51,
    },
    {
        "text": "وأخيراً, الرقم 123.",
        "value": 123,
    },
    {
        "text": "لقد تعلمت الأساسيات! حاول تحريك الخرزات بنفسك.\nبعد ذلك, انتقل إلى صفحة التدريب للممارسة.",
        "value": 0,
    },
]


class LearnPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)

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
        self._instruction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(14)
        self._instruction_label.setFont(font)
        self._instruction_label.setMinimumWidth(350)
        right_panel_layout.addWidget(self._instruction_label)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        nav_layout.setAlignment(Qt.AlignCenter)

        self._prev_button = QPushButton("السابق")
        self._prev_button.clicked.connect(self._go_prev)
        nav_layout.addWidget(self._prev_button)

        self._next_button = QPushButton("التالي")
        self._next_button.clicked.connect(self._go_next)
        nav_layout.addWidget(self._next_button)

        right_panel_layout.addLayout(nav_layout)
        root_layout.addLayout(right_panel_layout)

        self._update_step()

    def _update_step(self) -> None:
        step_data = TUTORIAL_STEPS[self._current_step]

        self._instruction_label.setText(step_data["text"])
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

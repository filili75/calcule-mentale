from __future__ import annotations

import time

from PySide6.QtCore import (
    QAbstractAnimation,
    QCoreApplication,
    QEvent,
    QEasingCurve,
    QPropertyAnimation,
    QPointF,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QGridLayout,
    QLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core import (
    ExerciseSequence,
    Operation,
    generate_sequence,
    load_progress,
    save_progress,
)
from src.models import ExerciseSettings, LEVEL_PRESETS
from src.widgets import SorobanView


class TrainingPage(QWidget):
    def __init__(self, show_soroban: bool = True) -> None:
        super().__init__()

        self._show_soroban = show_soroban
        self.soroban = SorobanView(columns=7)
        self.soroban.valueChanged.connect(self._update_soroban_value)
        self.soroban.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        if not self._show_soroban:
            self.soroban.hide()
        self._sync_soroban_size()

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "العربية", "Français"])

        self.level_combo = QComboBox()
        self._populate_level_combo()

        self.columns_combo = QComboBox()
        self.columns_combo.addItems(["5", "7", "9"])

        self.ops_spin = QSpinBox()
        self.ops_spin.setRange(5, 40)

        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.5, 3.0)
        self.delay_spin.setSingleStep(0.1)

        self.operation_label = QLabel("+")
        self.operation_label.setObjectName("OperationLabel")
        self.operation_label.setAlignment(Qt.AlignCenter)

        self.progress_label = QLabel()
        self.sequence_preview = QLabel()
        self.sequence_preview.setWordWrap(True)
        self.sequence_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.result_label = QLabel()
        if self._show_soroban:
            self.result_value = QLabel("-")
        else:
            self.result_value = QLineEdit()
            self.result_value.setReadOnly(True)
            self.result_value.setAlignment(Qt.AlignCenter)
            self.result_value.setMinimumWidth(120)
            self.result_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.result_value.setFocusPolicy(Qt.NoFocus)
        self.show_answer_button = QPushButton()

        self.start_button = QPushButton()
        self.pause_button = QPushButton()
        self.reset_button = QPushButton()
        for button in (
            self.start_button,
            self.pause_button,
            self.reset_button,
            self.show_answer_button,
        ):
            button.setMinimumHeight(36)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pause_button.setEnabled(False)
        if not self._show_soroban:
            self.show_answer_button.setEnabled(False)

        self.answer_input = QLineEdit()
        self.answer_input.setEnabled(False)
        self.check_button = QPushButton()
        self.check_button.setEnabled(False)

        self.feedback_label = QLabel()
        self.feedback_label.setObjectName("FeedbackLabel")
        self.prompt_label = QLabel()

        self.score_label = QLabel()
        self.time_label = QLabel()
        self.lifetime_label = QLabel()
        self.soroban_value_label = QLabel()

        self.operation_box = QGroupBox()
        self.settings_box = QGroupBox()
        self.controls_box = QGroupBox()
        self.answer_box = QGroupBox()
        self.score_box = QGroupBox()

        self.level_label = QLabel()
        self.columns_label = QLabel()
        self.ops_label = QLabel()
        self.delay_label = QLabel()
        self.ops_label = QLabel()
        self.delay_label = QLabel()

        self._sequence: ExerciseSequence | None = None
        self._operations: list[Operation] = []
        self._current_index = -1
        self._state = "idle"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._show_next_operation)

        self._replay_index = 0
        self._correct = 0
        self._wrong = 0
        self._total_time = 0.0
        self._session_start = 0.0
        self._paused_at: float | None = None
        self._paused_total = 0.0
        self._auto_advance = True
        self._show_answer = False
        self._soroban_press_pos: QPointF | None = None
        self._progress = load_progress()

        self._operation_glow = QGraphicsDropShadowEffect(self.operation_label)
        self._operation_glow.setBlurRadius(22)
        self._operation_glow.setOffset(0, 0)
        self._operation_glow.setColor(QColor("#F4A261"))
        self.operation_label.setGraphicsEffect(self._operation_glow)
        self._operation_anim = QPropertyAnimation(
            self._operation_glow, b"blurRadius", self
        )
        self._operation_anim.setDuration(280)
        self._operation_anim.setStartValue(36)
        self._operation_anim.setEndValue(14)
        self._operation_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._build_layout()
        self._wire_events()
        self._apply_level_defaults(self.level_combo.currentText())
        self.retranslate_ui()
        self._update_progress_label()
        self._sync_sequence_result_fonts()
        self._emphasize_settings_box()

    def changeEvent(self, event):
        if event.type() == event.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def retranslate_ui(self):
        self.operation_box.setTitle(self.tr("Sequence"))
        self.settings_box.setTitle(self.tr("Settings"))
        self.controls_box.setTitle(self.tr("Controls"))
        self.answer_box.setTitle(self.tr("Answer"))
        self.score_box.setTitle(self.tr("Score"))

        # Refresh level combo to update translations
        current_data = self.level_combo.currentData()
        self._populate_level_combo()
        if current_data:
            idx = self.level_combo.findData(current_data)
            if idx >= 0:
                self.level_combo.setCurrentIndex(idx)

        self.level_label.setText(self.tr("Level"))
        self.columns_label.setText(self.tr("Columns"))
        self.ops_label.setText(self.tr("Operations"))
        self.delay_label.setText(self.tr("Delay (s)"))
        self.result_label.setText(self.tr("Result"))

        self.start_button.setText(self.tr("Start"))
        self.pause_button.setText(self.tr("Pause"))
        self.reset_button.setText(self.tr("Reset"))
        self.check_button.setText(self.tr("Check"))
        self.show_answer_button.setText(self.tr("Answer"))
        
        self.answer_input.setPlaceholderText(self.tr("Type the result"))
        
        self.prompt_label.setText(self.tr("Ready?"))
        self._update_score_label()
        self.time_label.setText(
            self.tr("Time: %n s", "", int(round(self._total_time)))
        )

        self._update_soroban_value(self.soroban.get_value())
        self._update_progress_label()
        self._sync_sequence_result_fonts()
        
        if self._state == "idle":
            self.progress_label.setText("0/0")
            self.pause_button.setEnabled(False)
        
        if self._state == "paused":
            self.start_button.setEnabled(True)
            self.start_button.setText(self.tr("Resume"))
            self.pause_button.setEnabled(False)


    def _build_layout(self) -> None:
        if self._show_soroban:
            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(12, 10, 12, 12)
            root_layout.setSpacing(10)

            self.soroban_value_label.setAlignment(Qt.AlignCenter)
            self.soroban_value_label.setText("0")
            self.soroban_value_label.setMinimumHeight(64)
            self.soroban_value_label.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Fixed
            )
            self.soroban_value_label.setStyleSheet(
                "QLabel {"
                "background-color: #101214;"
                "color: #39D98A;"
                "border: 2px solid #1C1E21;"
                "border-radius: 14px;"
                "padding: 10px 24px;"
                "font-size: 32px;"
                "font-weight: 700;"
                "font-family: \"Segoe UI\", \"Consolas\", \"Courier New\", monospace;"
                "letter-spacing: 2px;"
                "}"
            )

            root_layout.addWidget(self.soroban, 1)
            root_layout.addWidget(self.soroban_value_label, 0, Qt.AlignHCenter)
            return

        root_layout = QHBoxLayout(self)
        root_layout.setSpacing(16)

        if self._show_soroban:
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(12)

            operation_layout = QVBoxLayout(self.operation_box)
            operation_layout.addWidget(self.operation_label)
            operation_layout.addWidget(self.progress_label)
            sequence_row = QHBoxLayout()
            sequence_row.setSpacing(8)
            sequence_row.addWidget(self.sequence_preview, 1)
            sequence_row.addWidget(self.result_label)
            sequence_row.addWidget(self.result_value)
            operation_layout.addLayout(sequence_row)

            settings_container = QWidget()
            settings_layout = QFormLayout(settings_container)
            settings_layout.addRow(self.level_label, self.level_combo)
            settings_layout.addRow(self.columns_label, self.columns_combo)
            settings_layout.addRow(self.ops_label, self.ops_spin)
            settings_layout.addRow(self.delay_label, self.delay_spin)
            settings_scroll = QScrollArea()
            settings_scroll.setWidgetResizable(True)
            settings_scroll.setFrameShape(QFrame.NoFrame)
            settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            settings_scroll.setWidget(settings_container)
            settings_box_layout = QVBoxLayout(self.settings_box)
            settings_box_layout.setContentsMargins(8, 6, 8, 8)
            settings_box_layout.addWidget(settings_scroll)
            self.settings_box.setMinimumHeight(380)
            self.settings_box.setMaximumHeight(380)

            controls_buttons = (
                self.start_button,
                self.pause_button,
                self.reset_button,
                self.show_answer_button,
            )
            controls_layout = QGridLayout(self.controls_box)
            controls_layout.setContentsMargins(8, 6, 8, 8)
            controls_layout.setHorizontalSpacing(10)
            controls_layout.setVerticalSpacing(8)
            positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
            for button, (row, column) in zip(controls_buttons, positions):
                controls_layout.addWidget(button, row, column)
            controls_layout.setColumnStretch(0, 1)
            controls_layout.setColumnStretch(1, 1)

            answer_layout = QVBoxLayout(self.answer_box)
            answer_layout.addWidget(self.prompt_label)
            answer_layout.addWidget(self.answer_input)
            answer_layout.addWidget(self.check_button)
            answer_layout.addWidget(self.feedback_label)

            score_layout = QVBoxLayout(self.score_box)
            score_layout.addWidget(self.score_label)
            score_layout.addWidget(self.time_label)
            score_layout.addWidget(self.lifetime_label)

            top_panel = QWidget()
            top_layout = QVBoxLayout(top_panel)
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(8)
            top_layout.addWidget(self.operation_box)
            top_layout.addWidget(self.controls_box)

            details_panel = QWidget()
            details_layout = QVBoxLayout(details_panel)
            details_layout.setContentsMargins(0, 0, 0, 0)
            details_layout.setSpacing(12)
            details_layout.addWidget(self.settings_box)
            details_layout.addWidget(self.answer_box)
            details_layout.addWidget(self.score_box)
            details_layout.addStretch(1)

            details_scroll = QScrollArea()
            details_scroll.setWidgetResizable(True)
            details_scroll.setFrameShape(QFrame.NoFrame)
            details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            details_scroll.setWidget(details_panel)

            right_layout.addWidget(top_panel)
            right_layout.addWidget(details_scroll, 1)
            
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(8)
            left_layout.addWidget(self.soroban, 0, Qt.AlignTop)
            left_layout.addWidget(self.soroban_value_label)
            left_layout.addStretch(1)
            root_layout.addWidget(left_panel)
            root_layout.addWidget(right_panel, 1)
        
        else:
            # Refactored layout for non-soroban mode
            main_content = QWidget()
            main_layout = QVBoxLayout(main_content)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(12)

            sidebar_content = QWidget()
            sidebar_layout = QVBoxLayout(sidebar_content)
            sidebar_layout.setContentsMargins(0, 0, 0, 0)
            sidebar_layout.setSpacing(12)
            sidebar_layout.setAlignment(Qt.AlignTop)

            # 1. Shrunken Sequence/Operation Box
            self.operation_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            operation_layout = QVBoxLayout(self.operation_box)
            self.progress_label.setAlignment(Qt.AlignCenter)
            self.operation_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            operation_layout.addWidget(self.operation_label, 1, Qt.AlignHCenter)
            operation_layout.addWidget(self.progress_label, 0, Qt.AlignHCenter)
            
            # 2. Compact Action Row
            self.answer_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            answer_layout = QVBoxLayout(self.answer_box)
            
            action_row_layout = QHBoxLayout()
            action_row_layout.addWidget(self.answer_input, 1)
            action_row_layout.addWidget(self.check_button)
            
            answer_layout.addWidget(self.prompt_label)
            answer_layout.addLayout(action_row_layout)
            answer_layout.addWidget(self.feedback_label)

            # 3. Score Box
            score_layout = QVBoxLayout(self.score_box)
            score_layout.addWidget(self.score_label)
            score_layout.addWidget(self.time_label)
            score_layout.addWidget(self.lifetime_label)

            # Assemble main content (left)
            main_layout.addWidget(self.operation_box, 1)
            main_layout.addWidget(self.answer_box)
            main_layout.addWidget(self.score_box)
            
            # 4. Sidebar (right)
            # Controls
            self.controls_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            controls_layout = QVBoxLayout(self.controls_box)
            controls_layout.setContentsMargins(10, 10, 10, 10)
            controls_layout.setSpacing(10)
            controls_layout.addWidget(self.start_button)
            controls_layout.addWidget(self.pause_button)
            controls_layout.addWidget(self.reset_button)
            controls_layout.addWidget(self.show_answer_button)
            
            # Settings
            self.settings_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            settings_container = QWidget()
            settings_layout = QFormLayout(settings_container)
            settings_layout.addRow(self.level_label, self.level_combo)
            settings_layout.addRow(self.ops_label, self.ops_spin)
            settings_layout.addRow(self.delay_label, self.delay_spin)
            settings_scroll = QScrollArea()
            settings_scroll.setWidgetResizable(True)
            settings_scroll.setFrameShape(QFrame.NoFrame)
            settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            settings_scroll.setWidget(settings_container)
            settings_box_layout = QVBoxLayout(self.settings_box)
            settings_box_layout.setContentsMargins(8, 6, 8, 8)
            settings_box_layout.addWidget(settings_scroll)

            # Assemble sidebar
            sidebar_layout.addWidget(self.controls_box)
            sidebar_layout.addWidget(self.settings_box)

            # Assemble root layout
            root_layout.addWidget(main_content, 1)
            root_layout.addWidget(sidebar_content, 0)

    def _wire_events(self) -> None:
        self.level_combo.activated[int].connect(self._on_level_changed)
        self.columns_combo.currentTextChanged.connect(self._on_columns_changed)
        self.start_button.clicked.connect(self.start_session)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.reset_button.clicked.connect(self.reset_session)
        self.check_button.clicked.connect(self.check_answer)
        self.answer_input.returnPressed.connect(self.check_answer)
        self.show_answer_button.clicked.connect(self.show_correct_answer)
        if self._show_soroban:
            self.soroban.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if self._show_soroban and obj is self.soroban.viewport():
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
                self._soroban_press_pos = event.position()
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.LeftButton:
                if self._soroban_press_pos is not None:
                    delta = event.position() - self._soroban_press_pos
                    if abs(delta.x()) + abs(delta.y()) < 4:
                        item = self.soroban.itemAt(event.position().toPoint())
                        if item is not None and hasattr(item, "bead_type"):
                            self.soroban.handle_bead_click(item)
                            self._soroban_press_pos = None
                            return True
                self._soroban_press_pos = None
        return super().eventFilter(obj, event)

    def _populate_level_combo(self) -> None:
        self.level_combo.clear()
        for key in LEVEL_PRESETS.keys():
            self.level_combo.addItem(self.tr(key), key)

    def _on_level_changed(self, index: int) -> None:
        # Wrapper to get data and call old logic
        data = self.level_combo.itemData(index)
        if data is not None:
            self._apply_level_defaults(data)

    def _apply_level_defaults(self, level_name: str) -> None:
        level = LEVEL_PRESETS[level_name]
        self.ops_spin.setRange(level.min_ops, level.max_ops)
        self.ops_spin.setValue(level.default_ops)
        self.delay_spin.setValue(level.delay_s)

    def _on_columns_changed(self, value: str) -> None:
        columns = int(value)
        if self._show_soroban:
            self.soroban.set_columns(columns)
            self.soroban.reset()
            self._sync_soroban_size()

    def _sync_soroban_size(self) -> None:
        if not self._show_soroban:
            return
        scene = self.soroban.scene()
        if scene is None:
            return
        rect = scene.sceneRect()
        min_size = self.soroban.minimumSize()
        min_width = max(int(rect.width()) + 12, min_size.width())
        min_height = max(int(rect.height()) + 12, min_size.height())
        self.soroban.setMinimumSize(min_width, min_height)
        self.soroban.setMaximumSize(16777215, 16777215)

    def _update_soroban_value(self, value: int) -> None:
        if not self._show_soroban:
            return
        self.soroban_value_label.setText(str(value))

    def _update_progress_label(self) -> None:
        attempts = self._progress.total_attempts
        time_s = self._progress.total_time_s
        attempts_text = self.tr("Saved: %n attempt(s)", "", attempts)
        time_text = self.tr("Time: %n s", "", int(round(time_s)))
        self.lifetime_label.setText(f"{attempts_text} | {time_text}")

    def _update_score_label(self) -> None:
        correct_text = self.tr("Correct: %n", "", self._correct)
        wrong_text = self.tr("Wrong: %n", "", self._wrong)
        self.score_label.setText(f"{correct_text} | {wrong_text}")

    def start_session(self) -> None:
        if self._state == "running" or self._state == "replaying":
            return
        if self._state == "paused":
            if self._paused_at is not None:
                self._paused_total += time.perf_counter() - self._paused_at
                self._paused_at = None
            self._timer.start(int(self.delay_spin.value() * 1000))
            self._state = "running"
            self._set_controls_enabled(False)
            self.start_button.setText(self.tr("Start"))
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.pause_button.setText(self.tr("Pause"))
            if not self._show_soroban:
                self.show_answer_button.setEnabled(False)
            return

        self.operation_label.setStyleSheet("")
        self._set_controls_enabled(False)
        self.start_button.setEnabled(False)
        self.start_button.setText(self.tr("Start"))
        self.pause_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        if not self._show_soroban:
            self.show_answer_button.setEnabled(False)

        self._sequence = self._create_sequence()
        self._operations = self._sequence.operations
        self._current_index = -1
        self._state = "running"
        self._session_start = time.perf_counter()
        self._paused_at = None
        self._paused_total = 0.0

        self.sequence_preview.setText(
            f"{self.tr('Sequence')}: " + " ".join(op.text() for op in self._operations)
        )
        self._reset_result_display()
        self.prompt_label.setText(self.tr("Watch the operations"))
        self.feedback_label.setText("")
        self.feedback_label.setProperty("status", None)
        self._update_feedback_style()
        self.answer_input.clear()
        self.answer_input.setEnabled(False)
        self.check_button.setEnabled(False)

        self._show_next_operation()
        self._timer.start(int(self.delay_spin.value() * 1000))
        

    def toggle_pause(self) -> None:
        if self._state != "running" and self._state != "paused":
            return
        if self._state == "running":
            self._timer.stop()
            self._state = "paused"
            self._paused_at = time.perf_counter()
            self._set_controls_enabled(True)
            self.start_button.setEnabled(True)
            self.start_button.setText(self.tr("Resume"))
            self.pause_button.setEnabled(False)
        elif self._state == "paused":
            if self._paused_at is not None:
                self._paused_total += time.perf_counter() - self._paused_at
                self._paused_at = None
            self._timer.start(int(self.delay_spin.value() * 1000))
            self._state = "running"
            self._set_controls_enabled(False)
            self.start_button.setEnabled(False)
            self.start_button.setText(self.tr("Start"))
            self.pause_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.pause_button.setText(self.tr("Pause"))

    def reset_session(self) -> None:
        self._timer.stop()
        self._state = "idle"
        self._current_index = -1
        self._sequence = None
        self._operations = []
        self._correct = 0
        self._wrong = 0
        self._total_time = 0.0
        self._paused_at = None
        self._paused_total = 0.0
        self.operation_label.setText("+")
        self.operation_label.setStyleSheet("")
        self.progress_label.setText("0/0")
        self.sequence_preview.setText("")
        self.prompt_label.setText(self.tr("Ready?"))
        self.feedback_label.setText("")
        self.feedback_label.setProperty("status", None)
        self._update_feedback_style()
        self.answer_input.clear()
        self.answer_input.setEnabled(False)
        self.check_button.setEnabled(False)
        self._reset_result_display()
        self.start_button.setEnabled(True)
        self.start_button.setText(self.tr("Start"))
        self.pause_button.setText(self.tr("Pause"))
        if not self._show_soroban:
            self.show_answer_button.setEnabled(False)
        if self._show_soroban:
            self.soroban.reset()
        self._update_score_label()
        self.time_label.setText(
            self.tr("Time: %n s", "", int(round(self._total_time)))
        )
        self._set_controls_enabled(True)
        self.pause_button.setEnabled(False)

    def _create_sequence(self) -> ExerciseSequence:
        settings = ExerciseSettings(
            level_name=self.level_combo.currentData(),
            columns=int(self.columns_combo.currentText()),
            operations_count=int(self.ops_spin.value()),
            delay_s=float(self.delay_spin.value()),
        )
        return generate_sequence(settings)

    def _animate_operation_label(self) -> None:
        if self._operation_anim.state() == QAbstractAnimation.Running:
            self._operation_anim.stop()
        self._operation_glow.setBlurRadius(36)
        self._operation_anim.start()

    def _show_next_operation(self) -> None:
        if self._state != "running":
            return

        self._current_index += 1
        if self._current_index < len(self._operations):
            operation = self._operations[self._current_index]
            self.operation_label.setText(operation.text())
            self._animate_operation_label()
            self.progress_label.setText(
                f"{self._current_index + 1}/{len(self._operations)}"
            )
        else:
            self._timer.stop()
            self._enter_answer_state()

    def _enter_answer_state(self) -> None:
        self._state = "awaiting"
        self.start_button.setEnabled(True)
        self.answer_input.setEnabled(True)
        self.check_button.setEnabled(True)
        self.answer_input.setFocus()
        self.prompt_label.setText(self.tr("Type the final result"))
        if not self._show_soroban:
            self.show_answer_button.setEnabled(True)

    def _update_feedback_style(self) -> None:
        self.feedback_label.style().unpolish(self.feedback_label)
        self.feedback_label.style().polish(self.feedback_label)

    def _reset_result_display(self) -> None:
        if self._show_soroban:
            self.result_value.setText("-")
            return
        # For non-soroban, result is now in operation_label, which is reset elsewhere

    def _sync_sequence_result_fonts(self) -> None:
        seq_font = self.sequence_preview.font()
        self.result_label.setFont(seq_font)
        self.result_value.setFont(seq_font)

    def _emphasize_settings_box(self) -> None:
        shadow = QGraphicsDropShadowEffect(self.settings_box)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 35))
        self.settings_box.setGraphicsEffect(shadow)

    def show_correct_answer(self) -> None:
        if self._show_soroban:
            result = self._calculate_sequence_result()
            if result is None:
                self.result_value.setText("-")
                return
            self.result_value.setText(str(result))
            return
        
        # Logic for non-soroban view
        if self._state not in ("awaiting", "idle"):
            return
            
        result = self._calculate_sequence_result()
        if result is None:
            return

        self.operation_label.setText(str(result))
        self.operation_label.setStyleSheet("color: #2CC985;")
        self.show_answer_button.setEnabled(False)

    def _calculate_sequence_result(self) -> int | None:
        if self._sequence is not None:
            return self._sequence.result
        if not self._operations:
            return None
        total = 0
        for operation in self._operations:
            total = operation.apply(total)
        return total

    def check_answer(self) -> None:
        if self._state != "awaiting" or self._sequence is None:
            return

        raw_value = self.answer_input.text().strip()
        try:
            user_value = int(raw_value)
        except ValueError:
            self.feedback_label.setText(self.tr("Please enter a number"))
            self.feedback_label.setProperty("status", "error")
            self._update_feedback_style()
            return

        correct = user_value == self._sequence.result
        if correct:
            self._correct += 1
            self.feedback_label.setText(self.tr("Correct!"))
            self.feedback_label.setProperty("status", "correct")
        else:
            self._wrong += 1
            if self._show_soroban:
                self.feedback_label.setText(
                    self.tr("Wrong. Answer: %n", "", self._sequence.result)
                )
            else:
                self.feedback_label.setText(self.tr("Wrong."))
            self.feedback_label.setProperty("status", "wrong")
        
        self._update_feedback_style()

        if self._paused_at is not None:
            self._paused_total += time.perf_counter() - self._paused_at
            self._paused_at = None
        elapsed = time.perf_counter() - self._session_start - self._paused_total
        self._total_time += elapsed
        self._update_score_label()
        self.time_label.setText(
            self.tr("Time: %n s", "", int(round(self._total_time)))
        )

        self._progress.record_attempt(correct, elapsed)
        save_progress(self._progress)
        self._update_progress_label()

        self._state = "idle"
        self._set_controls_enabled(True)
        self.answer_input.setEnabled(False)
        self.check_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.start_button.setText(self.tr("Start"))
        self.pause_button.setEnabled(False)
        if not self._show_soroban:
            self.show_answer_button.setEnabled(False)

        if not correct:
            self._replay_sequence_on_soroban()
        elif self._auto_advance:
            QTimer.singleShot(1200, self.start_session)

    def _replay_sequence_on_soroban(self) -> None:
        if not self._show_soroban:
            if self._auto_advance:
                QTimer.singleShot(1500, self.start_session)
            return
        if self._sequence is None:
            return
        
        self._state = "replaying"
        self._set_controls_enabled(False)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.soroban.reset(animated=True)
        
        self._replay_index = 0
        # Add a small delay before starting the replay
        QTimer.singleShot(400, self._show_next_replay_step)

    def _show_next_replay_step(self) -> None:
        if self._state != "replaying" or self._sequence is None:
            return

        if self._replay_index < len(self._operations):
            operation = self._operations[self._replay_index]
            
            # Calculate running total up to this point
            current_total = self._sequence.initial_value
            for i in range(self._replay_index + 1):
                current_total = self._operations[i].apply(current_total)

            self.operation_label.setText(operation.text())
            self._animate_operation_label()
            self.soroban.set_value(current_total, animated=True)
            
            self.progress_label.setText(
                f"{self.tr('Step')} {self._replay_index + 1}/{len(self._operations)}"
            )

            self._replay_index += 1
            # Use a longer delay for replay to make it easier to follow
            QTimer.singleShot(int(self.delay_spin.value() * 1000 * 1.5), self._show_next_replay_step)
        else:
            # Replay finished
            self._state = "idle"
            self._set_controls_enabled(True)
            self.start_button.setEnabled(True)
            self.start_button.setText(self.tr("Start"))
            self.pause_button.setEnabled(False)
            self.reset_button.setEnabled(True)
            self.progress_label.setText(f"{len(self._operations)}/{len(self._operations)}")
            if self._auto_advance:
                QTimer.singleShot(1500, self.start_session)
    
    def _set_controls_enabled(self, enabled: bool) -> None:
        self.level_combo.setEnabled(enabled)
        self.columns_combo.setEnabled(enabled)
        self.ops_spin.setEnabled(enabled)
        self.delay_spin.setEnabled(enabled)


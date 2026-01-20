from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .learn_page import LearnPage
from .training_page import TrainingPage


class MainWindow(QMainWindow):
    languageChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.tr("Mental Math"))

        container = QWidget()
        root_layout = QVBoxLayout(container)
        root_layout.setContentsMargins(14, 6, 14, 12)
        root_layout.setSpacing(10)

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        # -- Top Bar (Language, etc.) --
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(8)
        
        self.lang_button = QToolButton()
        self.lang_button.setText("🌐")
        self.lang_button.setPopupMode(QToolButton.InstantPopup)
        self.lang_button.setToolTip(self.tr("Change Language"))
        self.lang_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: transparent;
                padding: 4px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border-color: #ccc;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        
        lang_menu = QMenu(self)
        self.action_en = QAction("English", self)
        self.action_ar = QAction("العربية", self)
        self.action_fr = QAction("Français", self)
        
        self.action_en.triggered.connect(lambda: self.languageChanged.emit("English"))
        self.action_ar.triggered.connect(lambda: self.languageChanged.emit("العربية"))
        self.action_fr.triggered.connect(lambda: self.languageChanged.emit("Français"))
        
        lang_menu.addAction(self.action_en)
        lang_menu.addAction(self.action_ar)
        lang_menu.addAction(self.action_fr)
        
        self.lang_button.setMenu(lang_menu)

        self.title = QLabel(self.tr("Mental Math"))
        self.title.setObjectName("TitleMainLabel")
        self.title.setAlignment(Qt.AlignHCenter)

        self.subtitle = QLabel(self.tr("Tibihit Community School"))
        self.subtitle.setObjectName("TitleSubLabel")
        self.subtitle.setAlignment(Qt.AlignHCenter)

        self.train_button = QPushButton(self.tr("Training"))
        self.exercises_button = QPushButton(self.tr("Exercises"))
        self.learn_button = QPushButton(self.tr("Learn Soroban"))
        self.train_button.setMinimumWidth(120)
        self.exercises_button.setMinimumWidth(120)
        self.learn_button.setMinimumWidth(140)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        nav_layout.addWidget(self.train_button)
        nav_layout.addWidget(self.exercises_button)
        nav_layout.addWidget(self.learn_button)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.subtitle)

        top_bar_layout.addWidget(self.lang_button)
        top_bar_layout.addStretch(1)
        top_bar_layout.addLayout(title_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addLayout(nav_layout)

        header_layout.addLayout(top_bar_layout) # Add top bar at the very top

        self.stack = QStackedWidget()
        self.training_page = TrainingPage()
        self.exercises_page = TrainingPage(show_soroban=False)
        self.learn_page = LearnPage()

        self.stack.addWidget(self.training_page)
        self.stack.addWidget(self.exercises_page)
        self.stack.addWidget(self.learn_page)

        root_layout.addWidget(header_container)
        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(container)
        self.resize(1100, 700)

        self.train_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.exercises_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.learn_button.clicked.connect(lambda: self.stack.setCurrentIndex(2))

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.tr("Mental Math"))
        self.title.setText(self.tr("Mental Math"))
        self.subtitle.setText(self.tr("Tibihit Community School"))
        self.train_button.setText(self.tr("Training"))
        self.exercises_button.setText(self.tr("Exercises"))
        self.learn_button.setText(self.tr("Learn Soroban"))
        self.lang_button.setToolTip(self.tr("Change Language"))

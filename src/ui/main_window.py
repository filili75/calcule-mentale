from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from .learn_page import LearnPage
from .training_page import TrainingPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("الحساب الذهني")

        container = QWidget()
        root_layout = QVBoxLayout(container)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        title = QLabel("الحساب الذهني")
        title.setObjectName("TitleMainLabel")
        title.setAlignment(Qt.AlignHCenter)

        subtitle = QLabel("م.م تيبيهيت الجماعاتية")
        subtitle.setObjectName("TitleSubLabel")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.train_button = QPushButton("Training")
        self.learn_button = QPushButton("Learn Soroban")
        self.train_button.setMinimumWidth(120)
        self.learn_button.setMinimumWidth(140)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.train_button)
        button_layout.addWidget(self.learn_button)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addLayout(button_layout)

        self.stack = QStackedWidget()
        self.training_page = TrainingPage()
        self.learn_page = LearnPage()

        self.stack.addWidget(self.training_page)
        self.stack.addWidget(self.learn_page)

        root_layout.addWidget(header_container)
        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(container)
        self.resize(1100, 700)

        self.train_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.learn_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))

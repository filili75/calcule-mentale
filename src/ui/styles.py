from __future__ import annotations

from PySide6.QtGui import QFont


APP_STYLE = """
/* --- Main Window & Background --- */
QWidget {
    background-color: #F0F2F5; /* Light Grey/White background */
    color: #1C1E21; /* Dark text */
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}

/* --- Labels --- */
QLabel#TitleMainLabel {
    font-size: 28px;
    font-weight: bold;
    color: #1877F2; /* Standard Blue */
    margin-bottom: 4px;
}

QLabel#TitleSubLabel {
    font-size: 15px;
    font-weight: 600;
    color: #65676B; /* Grey subtext */
    margin-bottom: 10px;
}

/* --- Operation Display --- */
QLabel#OperationLabel {
    font-size: 56px;
    font-weight: bold;
    color: #1C1E21;
    background-color: #FFFFFF;
    border: 2px solid #E4E6EB;
    border-radius: 20px;
    min-width: 180px;
    min-height: 180px;
    max-width: 180px;
    max-height: 180px;
    padding: 0;
}

/* --- Feedback Label --- */
QLabel#FeedbackLabel {
    font-size: 20px;
    font-weight: bold;
    color: #1C1E21; 
}
QLabel#FeedbackLabel[status="correct"] {
    color: #42B72A; /* Green */
}
QLabel#FeedbackLabel[status="wrong"] {
    color: #FA383E; /* Red */
}
QLabel#FeedbackLabel[status="error"] {
    color: #F7B928; /* Yellow/Orange */
}

/* --- Buttons --- */
QPushButton {
    background-color: #E4E6EB;
    color: #050505;
    border: 1px solid #CED0D4;
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 38px;
}
QPushButton:hover {
    background-color: #D8DADF;
}
QPushButton:pressed {
    background-color: #1877F2;
    color: #FFFFFF;
    border-color: #1877F2;
}
QPushButton:disabled {
    background-color: #F0F2F5;
    color: #BCC0C4;
    border-color: #F0F2F5;
}

/* --- Controls (Inputs, Combos) --- */
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #FFFFFF;
    color: #1C1E21;
    border: 1px solid #CED0D4;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 32px;
}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border-color: #1877F2;
    background-color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* --- Group Boxes --- */
QGroupBox {
    border: 1px solid #CED0D4;
    border-radius: 12px;
    margin-top: 12px;
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    color: #65676B;
    font-weight: bold;
}

/* --- Soroban View --- */
QGraphicsView {
    background: transparent;
    border: 1px solid #CED0D4;
    border-radius: 16px;
}
"""


def apply_style(app) -> None:
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI", 10))

from __future__ import annotations

from PySide6.QtGui import QFont


APP_STYLE = """
QWidget {
    background-color: #F7E7D3;
    color: #2F2A24;
    font-family: "Trebuchet MS";
    font-size: 13px;
}
QLabel#TitleMainLabel {
    font-size: 24px;
    font-weight: bold;
    color: #2F2A24;
}
QLabel#TitleSubLabel {
    font-size: 14px;
    font-weight: 600;
    color: #5B4636;
}
QLabel#OperationLabel {
    font-size: 48px;
    font-weight: bold;
    color: #264653;
    background-color: qlineargradient(
        x1: 0,
        y1: 0,
        x2: 1,
        y2: 1,
        stop: 0 #FDF0E0,
        stop: 1 #F6DDBD
    );
    border: 3px solid #E9C46A;
    border-radius: 14px;
    min-width: 170px;
    min-height: 170px;
    max-width: 170px;
    max-height: 170px;
    padding: 0;
}
QLabel#FeedbackLabel {
    font-size: 18px;
    font-weight: bold;
}
QLabel#FeedbackLabel[status="correct"] {
    color: #2A9D8F;
}
QLabel#FeedbackLabel[status="wrong"] {
    color: #E76F51;
}
QLabel#FeedbackLabel[status="error"] {
    color: #B56576;
}
QPushButton {
    background-color: #F4A261;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: bold;
    min-height: 34px;
}
QPushButton:hover {
    background-color: #E76F51;
}
QPushButton:pressed {
    background-color: #D97A4A;
}
QPushButton:disabled {
    background-color: #DDBEA9;
    color: #7A6B60;
}
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #FFF7ED;
    border: 2px solid #CDB8A1;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 30px;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #E9C46A;
}
QGroupBox {
    border: 2px solid #E9C46A;
    border-radius: 10px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px 0 6px;
}
QGraphicsView {
    background: #FCEBD7;
    border: 2px solid #CDB8A1;
    border-radius: 12px;
}
"""


def apply_style(app) -> None:
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Trebuchet MS", 10))

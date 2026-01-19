from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from PySide6.QtCore import (
    QPointF,
    Qt,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QPainter
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
)

# Configuration dictionary for Soroban styling and geometry
SOROBAN_CONFIG = {
    "bead_radius": 13,
    "bead_gap": 6,
    "column_gap": 60,
    "margin_x": 30,
    "margin_y": 16,
    "bar_y": 90,
    "lower_gap": 18,
    "label_area_height": 28,
    "font_family": "Segoe UI",
    "font_size": 9,
    "animation_duration": 150,
    "bead_inactive_color": "#E76F51",
    "bead_active_color": "#2A9D8F",
    "bead_pen_color": "#7A3B2E",
    "bead_pen_width": 1.2,
    "frame_pen_color": "#CDB8A1",
    "frame_pen_width": 2,
    "bar_pen_color": "#8C6E5B",
    "bar_pen_width": 6,
    "rod_pen_color": "#9C7B65",
    "rod_pen_width": 4,
    "label_color": "#5B4636",
}


@dataclass
class ColumnState:
    top_active: bool = False
    lower_active: int = 0


class SorobanBeadItem(QGraphicsEllipseItem):
    def __init__(
        self,
        rect_x: float,
        rect_y: float,
        diameter: float,
        column_index: int,
        bead_type: str,
        lower_index: int | None,
        min_y: float,
        max_y: float,
        on_release,
        on_move=None,
    ) -> None:
        super().__init__(0, 0, diameter, diameter)
        self.setPos(rect_x, rect_y)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.OpenHandCursor)

        self._lock_x = rect_x
        self._min_y = min_y
        self._max_y = max_y
        self._on_release = on_release
        self._on_move = on_move

        self.column_index = column_index
        self.bead_type = bead_type
        self.lower_index = lower_index

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            new_pos = value
            if callable(self._on_move):
                return self._on_move(self, new_pos)
            new_y = min(max(new_pos.y(), self._min_y), self._max_y)
            return QPointF(self._lock_x, new_y)
        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.setCursor(Qt.OpenHandCursor)
        if callable(self._on_release):
            self._on_release(self)
        super().mouseReleaseEvent(event)


class SorobanView(QGraphicsView):
    valueChanged = Signal(int)

    def __init__(self, columns: int = 7, parent=None) -> None:
        super().__init__(parent)
        self._columns = max(1, columns)
        self._states: list[ColumnState] = []
        self._column_items: list[dict[str, object]] = []
        self._drag_adjusting = False

        # Load config into brushes and pens for frequent use
        self._bead_inactive_brush = QBrush(QColor(SOROBAN_CONFIG["bead_inactive_color"]))
        self._bead_active_brush = QBrush(QColor(SOROBAN_CONFIG["bead_active_color"]))
        self._bead_pen = QPen(
            QColor(SOROBAN_CONFIG["bead_pen_color"]), SOROBAN_CONFIG["bead_pen_width"]
        )

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(360, 260)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

        self._setup_scene()

    def set_columns(self, columns: int) -> None:
        self._columns = max(1, columns)
        self._setup_scene()
        self.valueChanged.emit(self.get_value())

    def reset(self, animated: bool = False) -> None:
        self._states = [ColumnState() for _ in range(self._columns)]
        for col_index in range(self._columns):
            self._apply_column_state(col_index, animated=animated)
        self.valueChanged.emit(self.get_value())

    def get_digits(self) -> list[int]:
        digits = []
        for state in self._states:
            digit = (5 if state.top_active else 0) + state.lower_active
            digits.append(digit)
        return digits

    def get_value(self) -> int:
        digits = self.get_digits()
        value = 0
        for digit in digits:
            value = value * 10 + digit
        return value

    def set_value(self, value: int, animated: bool = False) -> None:
        if value < 0:
            return

        s_value = str(value).zfill(self._columns)
        if len(s_value) > self._columns:
            s_value = s_value[-self._columns :]

        digits = [int(d) for d in s_value]

        for i, digit in enumerate(digits):
            self._states[i] = ColumnState(
                top_active=digit >= 5,
                lower_active=digit % 5,
            )
            self._apply_column_state(i, animated=animated)

        self.valueChanged.emit(self.get_value())

    def _setup_scene(self) -> None:
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self._states = [ColumnState() for _ in range(self._columns)]
        self._column_items = []

        geometry = self._calculate_geometry()
        self._create_frame(scene, geometry)

        for col in range(self._columns):
            self._create_column(scene, col, geometry)

        self.setSceneRect(0, 0, geometry["total_width"], geometry["total_height"])
        self._fit_in_view()

    def _calculate_geometry(self) -> dict:
        cfg = SOROBAN_CONFIG
        bead_radius = cfg["bead_radius"]
        bead_gap = cfg["bead_gap"]
        margin_y = cfg["margin_y"]
        bar_y = cfg["bar_y"]
        lower_gap = cfg["lower_gap"]

        bead_diameter = bead_radius * 2
        top_inactive_y = margin_y
        top_active_y = bar_y - bead_diameter - 6  # Small gap to the bar

        lower_active_start = bar_y + 6  # Small gap to the bar
        lower_active_positions = [
            lower_active_start + i * (bead_diameter + bead_gap) for i in range(4)
        ]
        lower_inactive_start = lower_active_positions[-1] + bead_diameter + lower_gap
        lower_inactive_positions = [
            lower_inactive_start + i * (bead_diameter + bead_gap) for i in range(4)
        ]

        base_height = lower_inactive_positions[-1] + bead_diameter + margin_y
        total_height = base_height + cfg["label_area_height"]
        total_width = (
            cfg["margin_x"] * 2
            + (self._columns - 1) * cfg["column_gap"]
            + bead_diameter
        )

        return {
            "bead_diameter": bead_diameter,
            "top_inactive_y": top_inactive_y,
            "top_active_y": top_active_y,
            "lower_active_positions": lower_active_positions,
            "lower_inactive_positions": lower_inactive_positions,
            "base_height": base_height,
            "total_height": total_height,
            "total_width": total_width,
        }

    def _create_frame(self, scene: QGraphicsScene, geometry: dict) -> None:
        cfg = SOROBAN_CONFIG
        pen = QPen(QColor(cfg["frame_pen_color"]), cfg["frame_pen_width"])
        scene.addRect(0, 0, geometry["total_width"], geometry["total_height"], pen)

        bar_pen = QPen(QColor(cfg["bar_pen_color"]), cfg["bar_pen_width"])
        scene.addLine(0, cfg["bar_y"], geometry["total_width"], cfg["bar_y"], bar_pen)

    def _create_column(
        self, scene: QGraphicsScene, col_index: int, geometry: dict
    ) -> None:
        cfg = SOROBAN_CONFIG
        bead_radius = cfg["bead_radius"]
        bead_diameter = geometry["bead_diameter"]

        x = cfg["margin_x"] + col_index * cfg["column_gap"]

        # --- Rod ---
        rod_pen = QPen(QColor(cfg["rod_pen_color"]), cfg["rod_pen_width"])
        scene.addLine(
            x + bead_radius,
            cfg["margin_y"],
            x + bead_radius,
            geometry["base_height"] - cfg["margin_y"],
            rod_pen,
        )

        # --- Top Bead ---
        top_bead = SorobanBeadItem(
            rect_x=x,
            rect_y=geometry["top_inactive_y"],
            diameter=bead_diameter,
            column_index=col_index,
            bead_type="top",
            lower_index=None,
            min_y=min(geometry["top_inactive_y"], geometry["top_active_y"]),
            max_y=max(geometry["top_inactive_y"], geometry["top_active_y"]),
            on_release=self._snap_bead,
            on_move=self._constrain_bead_move,
        )
        top_bead.setBrush(self._bead_inactive_brush)
        top_bead.setPen(self._bead_pen)
        scene.addItem(top_bead)

        # --- Lower Beads ---
        lower_beads: list[SorobanBeadItem] = []
        for idx in range(4):
            bead = SorobanBeadItem(
                rect_x=x,
                rect_y=geometry["lower_inactive_positions"][idx],
                diameter=bead_diameter,
                column_index=col_index,
                bead_type="lower",
                lower_index=idx,
                min_y=min(
                    geometry["lower_active_positions"][idx],
                    geometry["lower_inactive_positions"][idx],
                ),
                max_y=max(
                    geometry["lower_active_positions"][idx],
                    geometry["lower_inactive_positions"][idx],
                ),
                on_release=self._snap_bead,
                on_move=self._constrain_bead_move,
            )
            bead.setBrush(self._bead_inactive_brush)
            bead.setPen(self._bead_pen)
            scene.addItem(bead)
            lower_beads.append(bead)

        # --- Place Value Label ---
        place_value = 10 ** (self._columns - 1 - col_index)
        label_text = str(place_value)
        label_font = QFont(cfg["font_family"], cfg["font_size"])
        label_item = scene.addText(label_text, label_font)
        label_item.setDefaultTextColor(QColor(cfg["label_color"]))
        label_rect = label_item.boundingRect()
        label_x = x + bead_radius - (label_rect.width() / 2)
        label_item.setPos(label_x, geometry["base_height"] + 4)

        self._column_items.append(
            {
                "top_bead": top_bead,
                "lower_beads": lower_beads,
                "top_active_y": geometry["top_active_y"],
                "top_inactive_y": geometry["top_inactive_y"],
                "lower_active_positions": geometry["lower_active_positions"],
                "lower_inactive_positions": geometry["lower_inactive_positions"],
            }
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_in_view()

    def _fit_in_view(self) -> None:
        if not self.scene():
            return
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def _snap_bead(self, bead: SorobanBeadItem) -> None:
        column = bead.column_index
        state = self._states[column]
        items = self._column_items[column]

        if bead.bead_type == "top":
            top_active_y = items["top_active_y"]
            top_inactive_y = items["top_inactive_y"]
            midpoint = (top_active_y + top_inactive_y) / 2
            state.top_active = bead.pos().y() >= midpoint
        else:
            self._update_lower_state_from_positions(column)

        self._apply_column_state(column, animated=True)
        self.valueChanged.emit(self.get_value())

    def _update_lower_state_from_positions(self, column: int) -> None:
        state = self._states[column]
        items = self._column_items[column]
        lower_positions = items["lower_active_positions"]
        lower_inactive = items["lower_inactive_positions"]
        lower_beads = items["lower_beads"]

        active_count = 0
        for idx, bead in enumerate(lower_beads):
            midpoint = (lower_positions[idx] + lower_inactive[idx]) / 2
            if bead.pos().y() <= midpoint:
                active_count = idx + 1

        state.lower_active = active_count

    def _refresh_lower_bead_brushes(self, column: int) -> None:
        state = self._states[column]
        items = self._column_items[column]
        lower_beads = items["lower_beads"]

        for idx, bead in enumerate(lower_beads):
            is_active = idx < state.lower_active
            bead.setBrush(
                self._bead_active_brush if is_active else self._bead_inactive_brush
            )

    def _constrain_bead_move(self, bead: SorobanBeadItem, new_pos: QPointF) -> QPointF:
        new_y = min(max(new_pos.y(), bead._min_y), bead._max_y)
        if bead.bead_type != "lower":
            return QPointF(bead._lock_x, new_y)

        if self._drag_adjusting:
            return QPointF(bead._lock_x, new_y)

        column = bead.column_index
        items = self._column_items[column]
        lower_beads = items["lower_beads"]
        idx = bead.lower_index or 0
        spacing = SOROBAN_CONFIG["bead_radius"] * 2 + SOROBAN_CONFIG["bead_gap"]

        positions = [b.pos().y() for b in lower_beads]
        positions[idx] = new_y

        for i in range(idx - 1, -1, -1):
            desired = positions[i + 1] - spacing
            if positions[i] > desired:
                positions[i] = desired
            positions[i] = max(positions[i], lower_beads[i]._min_y)

        for i in range(idx + 1, len(lower_beads)):
            desired = positions[i - 1] + spacing
            if positions[i] < desired:
                positions[i] = desired
            positions[i] = min(positions[i], lower_beads[i]._max_y)

        self._drag_adjusting = True
        try:
            for i, other in enumerate(lower_beads):
                if other is bead:
                    continue
                other.setPos(other._lock_x, positions[i])
        finally:
            self._drag_adjusting = False

        self._update_lower_state_from_positions(column)
        self._refresh_lower_bead_brushes(column)
        self.valueChanged.emit(self.get_value())

        return QPointF(bead._lock_x, positions[idx])

    def _apply_column_state(self, column: int, animated: bool = False) -> None:
        state = self._states[column]
        items = self._column_items[column]

        animation_group = QParallelAnimationGroup(self)

        top_bead = items["top_bead"]
        top_y = items["top_active_y"] if state.top_active else items["top_inactive_y"]
        top_bead.setBrush(
            self._bead_active_brush if state.top_active else self._bead_inactive_brush
        )

        if animated:
            anim = QPropertyAnimation(top_bead, b"pos")
            anim.setEndValue(QPointF(top_bead.pos().x(), top_y))
            anim.setDuration(SOROBAN_CONFIG["animation_duration"])
            anim.setEasingCurve(QEasingCurve.OutCubic)
            animation_group.addAnimation(anim)
        else:
            top_bead.setPos(top_bead.pos().x(), top_y)

        lower_beads = items["lower_beads"]
        lower_active_positions = items["lower_active_positions"]
        lower_inactive_positions = items["lower_inactive_positions"]

        for idx, bead in enumerate(lower_beads):
            is_active = idx < state.lower_active
            target_y = lower_active_positions[idx] if is_active else lower_inactive_positions[idx]
            bead.setBrush(
                self._bead_active_brush if is_active else self._bead_inactive_brush
            )

            if animated:
                anim = QPropertyAnimation(bead, b"pos")
                anim.setEndValue(QPointF(bead.pos().x(), target_y))
                anim.setDuration(SOROBAN_CONFIG["animation_duration"])
                anim.setEasingCurve(QEasingCurve.OutCubic)
                animation_group.addAnimation(anim)
            else:
                bead.setPos(bead.pos().x(), target_y)
        
        if animated:
            animation_group.start(QParallelAnimationGroup.DeleteWhenStopped)


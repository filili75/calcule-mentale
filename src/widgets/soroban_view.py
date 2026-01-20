from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import (
    QPointF,
    Qt,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPen,
    QPainter,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)

# --- Configuration ---
SOROBAN_CONFIG = {
    # Dimensions
    "bead_radius": 14,
    "bead_gap": 6,
    "column_gap": 64,
    "margin_x": 40,
    "margin_y": 20,
    "bar_y": 100,
    "lower_gap": 24, 
    "label_area_height": 32,
    "font_family": "Segoe UI",
    "font_size": 12,
    "animation_duration": 250,

    # Colors (Light Theme / Old Style)
    "top_bead_active": "#ff7b72",     # Red
    "top_bead_inactive": "#57606a",   # Grey
    
    "lower_bead_active": "#58a6ff",   # Blue
    "lower_bead_inactive": "#57606a", # Grey
    
    "bead_border": "#24292f",         # Dark frame
    "bead_pen_width": 2.0,
    
    "frame_color": "#24292f",
    "frame_pen_width": 2,
    "bar_color": "#24292f",
    "bar_pen_width": 6,
    "rod_color": "#57606a",
    "rod_pen_width": 4,
    
    "label_color": "#24292f",
}


@dataclass
class ColumnState:
    top_active: bool = False
    lower_active: int = 0  # 0 to 4


class SorobanBeadItem(QGraphicsEllipseItem):
    """
    A single bead item. 
    It knows its range of motion and notifies the view on move/release.
    """
    def __init__(
        self,
        rect_x: float,
        rect_y: float,
        diameter: float,
        column_index: int,
        bead_type: str,     # "top" or "lower"
        lower_index: int | None, # 0 (top-most) to 3 (bottom-most) if lower
        min_y: float,
        max_y: float,
        view_reference,
    ) -> None:
        super().__init__(0, 0, diameter, diameter)
        self.setPos(rect_x, rect_y)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.OpenHandCursor)
        
        # Physics / Constraints
        self._lock_x = rect_x
        self._min_y = min_y
        self._max_y = max_y
        
        # Identity
        self.column_index = column_index
        self.bead_type = bead_type
        self.lower_index = lower_index
        
        # Reference to the main view for logic delegation
        self._view = view_reference
        self._press_pos: QPointF | None = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            new_pos = value
            # Constrain to vertical rail
            new_y = min(max(new_pos.y(), self._min_y), self._max_y)
            constrained_pos = QPointF(self._lock_x, new_y)
            
            # Delegate multi-bead logic to the view
            if self.scene() and self._view:
                return self._view.handle_bead_move(self, constrained_pos)
            
            return constrained_pos

        return super().itemChange(change, value)

    def mousePressEvent(self, event) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        self._press_pos = event.scenePos()
        self._dragged = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.setCursor(Qt.OpenHandCursor)
        if self._view:
            self._view.handle_bead_release(self)
        self._press_pos = None
        super().mouseReleaseEvent(event)
    
    def set_visual_active(self, active: bool):
        """Helper to create a nice gradient/glow effect."""
        cfg = SOROBAN_CONFIG
        if self.bead_type == "top":
            color = cfg["top_bead_active"] if active else cfg["top_bead_inactive"]
        else:
            color = cfg["lower_bead_active"] if active else cfg["lower_bead_inactive"]
            
        # Create a radial gradient for 3D look
        grad = QRadialGradient(self.rect().center(), self.rect().width() / 1.5)
        c = QColor(color)
        grad.setColorAt(0, c.lighter(130))
        grad.setColorAt(1, c)
        
        self.setBrush(QBrush(grad))


class SorobanView(QGraphicsView):
    valueChanged = Signal(int)

    def __init__(self, columns: int = 7, parent=None) -> None:
        super().__init__(parent)
        self._columns = max(1, columns)
        self._states: list[ColumnState] = []
        self._column_items: list[dict] = []
        self._drag_adjusting = False  # Lock to prevent recursion during move
        
        self._init_ui()
        self._setup_scene()
        self._preview_value = self.get_value()

    def _init_ui(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Transparent background
        self.setStyleSheet("background: transparent; border: none;")

    # --- Public API ---

    def set_columns(self, columns: int) -> None:
        self._columns = max(1, columns)
        self._setup_scene()
        self.update_score()

    def reset(self, animated: bool = False) -> None:
        self._states = [ColumnState() for _ in range(self._columns)]
        self._sync_visuals_to_state(animated=animated)
        self.update_score()

    def get_value(self) -> int:
        value = 0
        for state in self._states:
            digit = (5 if state.top_active else 0) + state.lower_active
            value = value * 10 + digit
        return value

    def set_value(self, value: int, animated: bool = False) -> None:
        if value < 0: return
        
        s_value = str(value).zfill(self._columns)
        if len(s_value) > self._columns:
            s_value = s_value[-self._columns:]
            
        digits = [int(d) for d in s_value]
        
        for i, digit in enumerate(digits):
            self._states[i] = ColumnState(
                top_active=digit >= 5,
                lower_active=digit % 5
            )
        
        self._sync_visuals_to_state(animated=animated)
        self.update_score()

    def update_score(self, value: int | None = None) -> None:
        if value is None:
            value = self.get_value()
        if value != self._preview_value:
            self._preview_value = value
            self.valueChanged.emit(value)

    # --- Interaction Logic ---

    def _digit_from_state(self, state: ColumnState) -> int:
        return (5 if state.top_active else 0) + state.lower_active

    def _is_top_active(self, items: dict, top_y: float) -> bool:
        mid_top = (items["top_active_y"] + items["top_inactive_y"]) / 2
        return top_y > mid_top

    def _count_active_lower(self, items: dict, lower_y_positions: list[float]) -> int:
        active_count = 0
        for i, y in enumerate(lower_y_positions):
            active_rest = items["lower_active_pos"][i]
            inactive_rest = items["lower_inactive_pos"][i]
            mid = (active_rest + inactive_rest) / 2
            if y < mid:
                active_count += 1
            else:
                break
        return active_count

    def _calculate_preview_value(
        self,
        column: int,
        lower_y_positions: list[float],
        top_y: float,
    ) -> int:
        value = 0
        for col in range(self._columns):
            if col == column:
                items = self._column_items[col]
                digit = (5 if self._is_top_active(items, top_y) else 0)
                digit += self._count_active_lower(items, lower_y_positions)
            else:
                digit = self._digit_from_state(self._states[col])
            value = value * 10 + digit
        return value

    def _update_preview_value(
        self,
        column: int,
        lower_y_positions: list[float],
        top_y: float,
    ) -> None:
        preview_value = self._calculate_preview_value(
            column, lower_y_positions, top_y
        )
        self.update_score(preview_value)

    def handle_bead_click(self, bead: SorobanBeadItem) -> None:
        column = bead.column_index
        state = self._states[column]

        if bead.bead_type == "top":
            state.top_active = not state.top_active
        else:
            if bead.lower_index is None:
                return
            if bead.lower_index < state.lower_active:
                state.lower_active = bead.lower_index
            else:
                state.lower_active = bead.lower_index + 1

        self._sync_visuals_to_state(animated=True)
        self.update_score()

    def handle_bead_move(self, bead: SorobanBeadItem, new_pos: QPointF) -> QPointF:
        """
        Called when a bead is dragged.
        Calculates physics: collisions and pushing other beads.
        """
        if self._drag_adjusting:
            return new_pos

        column = bead.column_index
        items = self._column_items[column]
        
        # 1. Top Bead Logic (Simple)
        if bead.bead_type == "top":
            lower_positions = [b.y() for b in items["lower_beads"]]
            self._preview_state(column, lower_positions, new_pos.y())
            self._update_preview_value(column, lower_positions, new_pos.y())
            return new_pos

        # 2. Lower Bead Logic (Robust Multi-pass)
        lower_beads = items["lower_beads"]
        idx = bead.lower_index
        spacing = SOROBAN_CONFIG["bead_radius"] * 2 + SOROBAN_CONFIG["bead_gap"]
        
        # Initialize positions with current state
        vals = [b.y() for b in lower_beads]
        vals[idx] = new_pos.y()
        
        # PASS 1: Drag Propagation
        for i in range(idx - 1, -1, -1):
            target = vals[i+1] - spacing
            if vals[i] > target: vals[i] = target
        for i in range(idx + 1, 4):
            target = vals[i-1] + spacing
            if vals[i] < target: vals[i] = target

        # PASS 2: Top Wall (Min Y)
        for i in range(4):
            limit_min = lower_beads[i]._min_y
            if i > 0: limit_min = max(limit_min, vals[i-1] + spacing)
            if vals[i] < limit_min: vals[i] = limit_min

        # PASS 3: Bottom Wall (Max Y)
        for i in range(3, -1, -1):
            limit_max = lower_beads[i]._max_y
            if i < 3: limit_max = min(limit_max, vals[i+1] - spacing)
            if vals[i] > limit_max: vals[i] = limit_max

        # Apply
        self._drag_adjusting = True
        try:
            for i, other_bead in enumerate(lower_beads):
                if i != idx: 
                    other_bead.setPos(other_bead.x(), vals[i])
        finally:
            self._drag_adjusting = False
            
        # Update preview colors
        self._preview_state(column, vals, items["top_bead"].y())
        self._update_preview_value(column, vals, items["top_bead"].y())

        return QPointF(bead.x(), vals[idx])

    def handle_bead_release(self, bead: SorobanBeadItem):
        """
        Snap to grid.
        Determine new logical state based on positions, then animate to perfect positions.
        """
        column = bead.column_index
        items = self._column_items[column]
        
        # Update State
        state = self._states[column]
        
        if bead.bead_type == "top":
            state.top_active = self._is_top_active(items, bead.y())
        else:
            lower_beads = items["lower_beads"]
            lower_positions = [b.y() for b in lower_beads]
            state.lower_active = self._count_active_lower(items, lower_positions)
            
        # Snap visuals
        self._sync_visuals_to_state(animated=True)
        self.update_score()

    def _preview_state(self, col: int, lower_y_positions: list[float], top_y: float):
        """Update colors during drag without committing state"""
        items = self._column_items[col]
        
        # Preview Top
        top_is_active = self._is_top_active(items, top_y)
        items["top_bead"].set_visual_active(top_is_active)
        
        # Preview Lower
        active_count = self._count_active_lower(items, lower_y_positions)
        for i, bead in enumerate(items["lower_beads"]):
            bead.set_visual_active(i < active_count)

    def _sync_visuals_to_state(self, animated: bool = False):
        """Moves beads to their canonical positions based on logical state."""
        cfg = SOROBAN_CONFIG
        
        for col in range(self._columns):
            state = self._states[col]
            items = self._column_items[col]
            
            # 1. Top Bead
            target_y = items["top_active_y"] if state.top_active else items["top_inactive_y"]
            self._move_bead(items["top_bead"], target_y, animated, state.top_active)
            
            # 2. Lower Beads
            for i, bead in enumerate(items["lower_beads"]):
                is_active = i < state.lower_active
                target_y = items["lower_active_pos"][i] if is_active else items["lower_inactive_pos"][i]
                self._move_bead(bead, target_y, animated, is_active)

    def _move_bead(self, bead, target_y, animated, active_state):
        bead.set_visual_active(active_state)
        if animated:
            anim = QPropertyAnimation(bead, b"pos", self)
            anim.setEndValue(QPointF(bead.x(), target_y))
            anim.setDuration(SOROBAN_CONFIG["animation_duration"])
            anim.setEasingCurve(QEasingCurve.OutBack) # Bouncy snap
            bead._anim = anim # Keep ref
            anim.start()
        else:
            bead.setPos(bead.x(), target_y)

    # --- Setup & Geometry ---

    def _setup_scene(self) -> None:
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self._states = [ColumnState() for _ in range(self._columns)]
        self._column_items = []
        
        geo = self._calculate_geometry()
        
        # Draw Frame & Bar
        pen_frame = QPen(QColor(SOROBAN_CONFIG["frame_color"]), SOROBAN_CONFIG["frame_pen_width"])
        scene.addRect(0, 0, geo["total_width"], geo["total_height"], pen_frame)
        
        pen_bar = QPen(QColor(SOROBAN_CONFIG["bar_color"]), SOROBAN_CONFIG["bar_pen_width"])
        scene.addLine(0, SOROBAN_CONFIG["bar_y"], geo["total_width"], SOROBAN_CONFIG["bar_y"], pen_bar)
        
        # Create Columns
        for i in range(self._columns):
            self._create_column(scene, i, geo)
            
        self.setSceneRect(0, 0, geo["total_width"], geo["total_height"])
        self._fit_in_view()

    def _calculate_geometry(self) -> dict:
        cfg = SOROBAN_CONFIG
        dia = cfg["bead_radius"] * 2
        
        # TOP DECK (Header)
        top_inactive_y = cfg["margin_y"]
        top_active_y = cfg["bar_y"] - dia - 4 
        
        # LOWER DECK
        lower_active_start = cfg["bar_y"] + 4 
        lower_active_pos = []
        for i in range(4):
            pos = lower_active_start + i * (dia + cfg["bead_gap"])
            lower_active_pos.append(pos)
            
        lower_inactive_start = lower_active_pos[-1] + cfg["lower_gap"]
        lower_inactive_pos = []
        for i in range(4):
            pos = lower_inactive_start + i * (dia + cfg["bead_gap"])
            lower_inactive_pos.append(pos)
            
        base_height = lower_inactive_pos[-1] + dia + cfg["margin_y"]
        total_height = base_height + cfg["label_area_height"]
        total_width = cfg["margin_x"]*2 + (self._columns-1)*cfg["column_gap"] + dia
        
        return {
            "top_inactive_y": top_inactive_y,
            "top_active_y": top_active_y,
            "lower_active_pos": lower_active_pos,
            "lower_inactive_pos": lower_inactive_pos,
            "total_height": total_height,
            "total_width": total_width,
            "bead_diameter": dia
        }

    def _create_column(self, scene: QGraphicsScene, col_index: int, geo: dict):
        cfg = SOROBAN_CONFIG
        x = cfg["margin_x"] + col_index * cfg["column_gap"]
        
        # Rod
        pen_rod = QPen(QColor(cfg["rod_color"]), cfg["rod_pen_width"], Qt.SolidLine, Qt.RoundCap)
        scene.addLine(
            x + cfg["bead_radius"], 
            cfg["margin_y"], 
            x + cfg["bead_radius"], 
            geo["total_height"] - cfg["label_area_height"] - cfg["margin_y"], 
            pen_rod
        )
        
        bead_pen = QPen(QColor(cfg["bead_border"]), cfg["bead_pen_width"])
        
        # Top Bead
        top_bead = SorobanBeadItem(
            rect_x = x,
            rect_y = geo["top_inactive_y"],
            diameter = geo["bead_diameter"],
            column_index = col_index,
            bead_type = "top",
            lower_index = None,
            min_y = geo["top_inactive_y"], 
            max_y = geo["top_active_y"],   
            view_reference = self
        )
        top_bead.setPen(bead_pen)
        scene.addItem(top_bead)
        
        # Lower Beads
        lower_beads = []
        for i in range(4):
            l_bead = SorobanBeadItem(
                rect_x = x,
                rect_y = geo["lower_inactive_pos"][i],
                diameter = geo["bead_diameter"],
                column_index = col_index,
                bead_type = "lower",
                lower_index = i,
                min_y = geo["lower_active_pos"][i],
                max_y = geo["lower_inactive_pos"][i],
                view_reference = self
            )
            l_bead.setPen(bead_pen)
            scene.addItem(l_bead)
            lower_beads.append(l_bead)
            
        # Label
        place_val = 10**(self._columns - 1 - col_index)
        t = scene.addText(str(place_val), QFont(cfg["font_family"], 9))
        t.setDefaultTextColor(QColor(cfg["label_color"]))
        
        # center text
        br = t.boundingRect()
        t.setPos(x + cfg["bead_radius"] - br.width()/2, geo["total_height"] - cfg["label_area_height"])
        
        self._column_items.append({
            "top_bead": top_bead,
            "lower_beads": lower_beads,
            "top_active_y": geo["top_active_y"],
            "top_inactive_y": geo["top_inactive_y"],
            "lower_active_pos": geo["lower_active_pos"],
            "lower_inactive_pos": geo["lower_inactive_pos"]
        })
        
        # Init visual state
        self._preview_state(col_index, [b.y() for b in lower_beads], top_bead.y())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_in_view()

    def _fit_in_view(self):
        if self.scene():
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

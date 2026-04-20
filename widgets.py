import shutil
from io import BytesIO
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QFrame, QFileDialog, QPushButton, QSlider
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal
from PIL import Image

TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

# color palette — warm ivory / antique gold theme
COLOR_PRIMARY       = "#90662C"
COLOR_PRIMARY_HOVER = "#4F3107"
COLOR_PRIMARY_LIGHT = "#FBF7EF"

COLOR_BG            = "#F7F4EF"
COLOR_SURFACE       = "#FFFFFF"
COLOR_SURFACE_ALT   = "#FAF8F5"

COLOR_SIDEBAR_BORDER = "#EAE6DF"
COLOR_SIDEBAR_ITEM   = "#F5F2EC"

COLOR_BORDER        = "#D8D2C8"
COLOR_BORDER_FOCUS  = "#C8A84B"

COLOR_TEXT          = "#1A1A1A"
COLOR_TEXT_MUTED    = "#7A7570"
COLOR_TEXT_LIGHT    = "#C5BEB4"

COLOR_DANGER        = "#C0392B"
COLOR_DANGER_LIGHT  = "#FDEDEC"
COLOR_SUCCESS       = "#2A7A54"

# short aliases used in ui_main.py
BG        = COLOR_BG
NAVY      = COLOR_PRIMARY
NAVY_LITE = COLOR_PRIMARY_HOVER
ACCENT    = COLOR_PRIMARY
BORDER    = COLOR_BORDER
TEXT      = COLOR_TEXT
SUBTEXT   = COLOR_TEXT_MUTED
WHITE     = COLOR_SURFACE
DANGER    = COLOR_DANGER
SUCCESS   = COLOR_SUCCESS
CARD_BG   = COLOR_SURFACE


class ImageUploadBox(QWidget):
    image_selected = pyqtSignal(str, str)  # (view_type, file_path)

    VIEW_LABELS = {
        "front":  "Front View",
        "back":   "Back View",
        "design": "Fabric Closeup",
    }

    def __init__(self, view_type: str, parent=None):
        super().__init__(parent)
        self.view_type      = view_type
        self.image_path     = None
        self.original_image = None
        self._rotated_image = None  # cached so get_path() doesn't re-rotate on generate
        self.rotation_angle = 0
        self.setFixedSize(160, 230)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.frame = QFrame()
        self.frame.setObjectName("uploadFrame")
        self._apply_default_frame_style()

        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(8, 8, 8, 8)
        inner.setSpacing(6)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(140, 130)
        self.preview_label.setStyleSheet("border: none; background: transparent;")
        self._show_plus()

        self.name_label = QLabel(self.VIEW_LABELS.get(self.view_type, self.view_type))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 600; border: none;"
        )

        self.rotation_container = QWidget()
        self.rotation_container.setStyleSheet("border: none; background: transparent;")
        rotation_layout = QVBoxLayout(self.rotation_container)
        rotation_layout.setContentsMargins(0, 4, 0, 0)
        rotation_layout.setSpacing(2)

        self.angle_label = QLabel("0°")
        self.angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.angle_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 10px; border: none;"
        )

        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(-20, 20)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rotation_slider.setTickInterval(15)
        self.rotation_slider.setFixedWidth(130)
        self.rotation_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLOR_BORDER};
                height: 4px;
                background: {COLOR_SURFACE_ALT};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT};
                border: 1px solid {COLOR_BORDER};
                width: 14px;
                height: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLOR_PRIMARY_HOVER};
            }}
            QSlider::sub-page:horizontal {{
                background: {ACCENT};
                border-radius: 2px;
            }}
        """)
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)

        rotation_layout.addWidget(self.angle_label)
        rotation_layout.addWidget(self.rotation_slider, 0, Qt.AlignmentFlag.AlignCenter)
        self.rotation_container.hide()

        inner.addWidget(self.preview_label)
        inner.addWidget(self.name_label)
        inner.addWidget(self.rotation_container)
        layout.addWidget(self.frame)

    def _apply_default_frame_style(self):
        self.frame.setStyleSheet(f"""
            QFrame#uploadFrame {{
                border: 2px dashed {COLOR_BORDER};
                border-radius: 10px;
                background: {COLOR_SURFACE};
            }}
            QFrame#uploadFrame:hover {{
                border-color: {COLOR_PRIMARY};
                background: {COLOR_PRIMARY_LIGHT};
            }}
        """)

    def _show_plus(self):
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("＋")
        self.preview_label.setStyleSheet(
            f"color: {COLOR_TEXT_LIGHT}; font-size: 36px; font-weight: 200;"
            " border: none; background: transparent;"
        )

    def _show_preview(self, path: str):
        try:
            self.original_image = Image.open(path)
            # JPEG doesn't support alpha, so flatten to RGB
            if self.original_image.mode != "RGB":
                self.original_image = self.original_image.convert("RGB")
        except Exception as e:
            print(f"Error loading image: {e}")
            return

        self._update_preview()
        self.preview_label.setStyleSheet("border: none; background: transparent;")
        self.frame.setStyleSheet(f"""
            QFrame#uploadFrame {{
                border: 2px solid {COLOR_PRIMARY};
                border-radius: 10px;
                background: {COLOR_SURFACE};
            }}
        """)
        self.rotation_container.show()

    def _update_preview(self):
        if self.original_image is None:
            return

        # negative angle because PIL rotates counter-clockwise by default
        self._rotated_image = self.original_image.rotate(
            -self.rotation_angle, expand=True, fillcolor=(255, 255, 255)
        )

        # write to BytesIO instead of a temp file — avoids disk I/O on every slider drag
        buf = BytesIO()
        self._rotated_image.save(buf, format="JPEG", quality=85)
        pix = QPixmap.fromImage(QImage.fromData(buf.getvalue()))
        if not pix.isNull():
            scaled = pix.scaled(
                136, 126,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)
            self.preview_label.setText("")

    def _on_rotation_changed(self, value):
        self.rotation_angle = value
        self.angle_label.setText(f"{value}°")
        self._update_preview()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self.VIEW_LABELS.get(self.view_type, self.view_type)}",
            "", "Images (*.jpg *.jpeg *.png *.webp)"
        )
        if path:
            self._accept(path)

    def _accept(self, src_path: str):
        ext      = Path(src_path).suffix
        dst_name = f"upload_{id(self)}_{self.view_type}{ext}"
        dst_path = str(TEMP_DIR / dst_name)
        shutil.copy2(src_path, dst_path)
        self.image_path = dst_path
        self._show_preview(src_path)
        self.image_selected.emit(self.view_type, dst_path)

    def clear(self):
        self.image_path     = None
        self.original_image = None
        self._rotated_image = None
        self.rotation_angle = 0
        self.rotation_slider.setValue(0)
        self.rotation_container.hide()
        self._show_plus()
        self._apply_default_frame_style()

    def get_path(self) -> str | None:
        if self.image_path is None:
            return None
        if self.rotation_angle == 0:
            return self.image_path
        # reuse the already-rotated PIL image cached by _update_preview
        src = self._rotated_image or self.original_image
        if src is None:
            return self.image_path
        try:
            ext = Path(self.image_path).suffix
            out = str(TEMP_DIR / f"upload_{id(self)}_{self.view_type}_rotated{ext}")
            src.save(out, quality=98)
            return out
        except Exception as e:
            print(f"Error saving rotated image: {e}")
            return self.image_path


class StyledLineEdit(QWidget):
    """Label stacked above a QLineEdit — used for Style/Fabric/GSM fields."""

    def __init__(self, label: str, placeholder: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 600;")

        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 7px;
                padding: 7px 12px;
                background: {COLOR_SURFACE};
                color: {COLOR_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_BORDER_FOCUS};
            }}
        """)
        layout.addWidget(lbl)
        layout.addWidget(self.field)

    def text(self) -> str:
        return self.field.text().strip()

    def setText(self, t: str):
        self.field.setText(t)

    def clear(self):
        self.field.clear()


class GarmentPageCard(QFrame):
    remove_requested = pyqtSignal(object)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("garmentCard")
        self.setStyleSheet(f"""
            QFrame#garmentCard {{
                background: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 14px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        self._page_label = QLabel(f"Garment {self.index}")
        self._page_label.setStyleSheet(
            f"color: {COLOR_PRIMARY}; font-size: 13px; font-weight: 700;"
        )

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(26, 26)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLOR_TEXT_LIGHT};
                border: none;
                font-size: 14px;
                border-radius: 13px;
            }}
            QPushButton:hover {{
                background: {COLOR_DANGER_LIGHT};
                color: {COLOR_DANGER};
            }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        header.addWidget(self._page_label)
        header.addStretch()
        header.addWidget(remove_btn)

        boxes_row = QHBoxLayout()
        boxes_row.setSpacing(14)
        self.boxes: dict[str, ImageUploadBox] = {}
        for view in ("front", "back", "design"):
            box = ImageUploadBox(view)
            self.boxes[view] = box
            boxes_row.addWidget(box)
        boxes_row.addStretch()

        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(12)
        self.style_input  = StyledLineEdit("Style No", "e.g. ST-2024-001")
        self.fabric_input = StyledLineEdit("Fabric",   "e.g. 95% Poly 5% Spandex")
        self.gsm_input    = StyledLineEdit("GSM",      "e.g. 180")
        self.gsm_input.setFixedWidth(120)

        inputs_row.addWidget(self.style_input,  2)
        inputs_row.addWidget(self.fabric_input, 3)
        inputs_row.addWidget(self.gsm_input,    1)

        root.addLayout(header)
        root.addLayout(boxes_row)
        root.addLayout(inputs_row)

    def get_data(self) -> dict:
        return {
            "images": {
                view: box.get_path()
                for view, box in self.boxes.items()
                if box.get_path()
            },
            "style":  self.style_input.text(),
            "fabric": self.fabric_input.text(),
            "gsm":    self.gsm_input.text(),
        }

    def is_empty(self) -> bool:
        return not any(box.get_path() for box in self.boxes.values())

    def update_index(self, idx: int):
        self.index = idx
        self._page_label.setText(f"Garment {idx}")


class CatalogHistoryItem(QFrame):
    open_requested = pyqtSignal(str)

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        name = Path(pdf_path).stem.replace("_", " ").title()

        self.setObjectName("historyItem")
        self.setStyleSheet(f"""
            QFrame#historyItem {{
                background: {COLOR_SIDEBAR_ITEM};
                border: 1px solid {COLOR_SIDEBAR_BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QFrame#historyItem:hover {{
                border-color: {COLOR_PRIMARY};
                background: {COLOR_PRIMARY_LIGHT};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        icon = QLabel("📄")
        icon.setStyleSheet("font-size: 18px; border: none;")

        title = QLabel(name)
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 11px; font-weight: 600; border: none;"
        )
        title.setWordWrap(True)

        lay.addWidget(icon)
        lay.addWidget(title)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.pdf_path)

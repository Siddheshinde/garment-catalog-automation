import os
import subprocess
import sys
import traceback
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QScrollArea,
    QFrame, QMessageBox, QFileDialog, QDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence, QPixmap, QIcon

APP_ROOT = Path(__file__).parent.resolve()

from widgets import (
    GarmentPageCard, CatalogHistoryItem,
    BG, NAVY, NAVY_LITE, ACCENT, BORDER, TEXT, SUBTEXT, WHITE,
)
from backend_wrapper import generate_catalog

OUTPUT_DIR = Path(__file__).parent.resolve() / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class CatalogWorker(QThread):
    finished = pyqtSignal(str, list)  # (pdf_path, layout_paths)
    failed   = pyqtSignal(str)

    def __init__(self, pages: list[dict], title: str = ""):
        super().__init__()
        self.pages = pages
        self.title = title

    def run(self):
        try:
            pdf_path, layout_paths = generate_catalog(self.pages, self.title)
            self.finished.emit(pdf_path, layout_paths)
        except Exception as e:
            full_error = traceback.format_exc()
            self.failed.emit(f"{e}\n\n--- Full traceback ---\n{full_error}")


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background: {NAVY};
                border: none;
            }}
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        brand = QFrame()
        brand.setFixedHeight(72)
        brand.setStyleSheet(f"background: {NAVY_LITE};")
        brand_lay = QHBoxLayout(brand)
        brand_lay.setContentsMargins(16, 0, 16, 0)
        brand_lay.setSpacing(10)

        logo_path = APP_ROOT / "app_logo.png"
        if logo_path.exists():
            icon = QLabel()
            pix = QPixmap(str(logo_path)).scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon.setPixmap(pix)
            icon.setStyleSheet("border: none; background: transparent;")
        else:
            icon = QLabel("✦")
            icon.setStyleSheet("color: #A8C4E8; font-size: 20px;")
        title = QLabel("Catalog Studio")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        brand_lay.addWidget(icon)
        brand_lay.addWidget(title)
        brand_lay.addStretch()

        section_lbl = QLabel("PREVIOUS CATALOGS")
        section_lbl.setContentsMargins(20, 18, 20, 8)
        section_lbl.setStyleSheet(
            "color: #FFFFFF; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(12, 4, 12, 12)
        self.history_layout.setSpacing(8)
        self.history_layout.addStretch()

        self.history_scroll.setWidget(self.history_container)

        self.empty_label = QLabel("No catalogs yet.\nGenerate your first!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #4A6FA5; font-size: 11px;")
        self.empty_label.setWordWrap(True)
        self.empty_label.setContentsMargins(16, 20, 16, 0)

        root.addWidget(brand)
        root.addWidget(section_lbl)
        root.addWidget(self.empty_label)
        root.addWidget(self.history_scroll, 1)

        self._load_history()

    def _load_history(self):
        pdfs = sorted(OUTPUT_DIR.glob("*.pdf"), key=os.path.getmtime, reverse=True)
        if pdfs:
            self.empty_label.hide()
        for pdf in pdfs[:10]:
            thumb = OUTPUT_DIR / f"{pdf.stem}_thumb.jpg"
            self._add_item(str(pdf), str(thumb) if thumb.exists() else "")

    def add_catalog(self, pdf_path: str, thumb_path: str = ""):
        self.empty_label.hide()
        self._add_item(pdf_path, thumb_path, prepend=True)

    def _add_item(self, pdf_path: str, thumb_path: str = "", prepend: bool = False):
        item = CatalogHistoryItem(pdf_path, thumb_path)
        item.open_requested.connect(self._open_pdf)
        if prepend:
            self.history_layout.insertWidget(0, item)
        else:
            # insert before the trailing stretch
            self.history_layout.insertWidget(self.history_layout.count() - 1, item)

    @staticmethod
    def _open_pdf(path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(None, "Cannot open PDF", str(e))


class WorkArea(QWidget):
    catalog_generated = pyqtSignal(str, str)  # (pdf_path, thumb_path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")
        self._cards: list[GarmentPageCard] = []
        self._worker = None
        self._toast  = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(72)
        topbar.setStyleSheet(f"background: {WHITE}; border-bottom: 1px solid {BORDER};")
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(28, 0, 28, 0)
        topbar_lay.setSpacing(14)

        heading = QLabel("New Catalog")
        heading.setStyleSheet(f"color: {TEXT}; font-size: 18px; font-weight: 700;")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Catalog title (optional)")
        self.title_input.setFixedWidth(280)
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                padding: 8px 14px;
                background: {BG};
                color: {TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)

        self.gen_btn = QPushButton("Generate PDF")
        self.gen_btn.setFixedHeight(40)
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.setStyleSheet(self._gen_btn_style())
        self.gen_btn.clicked.connect(self._on_generate)

        topbar_lay.addWidget(heading)
        topbar_lay.addWidget(self.title_input)
        topbar_lay.addStretch()
        topbar_lay.addWidget(self.gen_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {BG}; }}
            QScrollBar:vertical {{
                background: {BG}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER}; border-radius: 4px; min-height: 20px;
            }}
        """)

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet(f"background: {BG};")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(28, 24, 28, 24)
        self.cards_layout.setSpacing(16)

        self.scroll.setWidget(self.cards_widget)

        bottom = QFrame()
        bottom.setFixedHeight(64)
        bottom.setStyleSheet(f"background: {WHITE}; border-top: 1px solid {BORDER};")
        bottom_lay = QHBoxLayout(bottom)
        bottom_lay.setContentsMargins(28, 0, 28, 0)
        bottom_lay.setSpacing(10)

        btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1.5px solid {ACCENT};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #EFF6FF; }}
        """

        self.add_page_btn = QPushButton("＋  Add Garment")
        self.add_page_btn.setFixedHeight(38)
        self.add_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_page_btn.setStyleSheet(btn_style)
        self.add_page_btn.clicked.connect(self._add_card)

        self.import_btn = QPushButton("📁  Import Folder")
        self.import_btn.setFixedHeight(38)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setStyleSheet(btn_style)
        self.import_btn.clicked.connect(self._batch_import)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")

        bottom_lay.addWidget(self.add_page_btn)
        bottom_lay.addWidget(self.import_btn)
        bottom_lay.addStretch()
        bottom_lay.addWidget(self.status_label)

        root.addWidget(topbar)
        root.addWidget(self.scroll, 1)
        root.addWidget(bottom)

        # Ctrl+Enter triggers generate
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_generate)

        self._add_card()

    def _add_card(self, data: dict | None = None):
        card = GarmentPageCard(len(self._cards) + 1)
        card.remove_requested.connect(self._remove_card)

        if data:
            card.style_input.setText(data.get("style", ""))
            card.fabric_input.setText(data.get("fabric", ""))
            card.gsm_input.setText(data.get("gsm", ""))
            for view, path in data.get("images", {}).items():
                if path and Path(path).exists() and view in card.boxes:
                    card.boxes[view]._accept(path)

        self._cards.append(card)
        self.cards_layout.addWidget(card)
        self._update_status()

        # scroll to the new card after Qt finishes laying it out
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _remove_card(self, card: GarmentPageCard):
        if len(self._cards) == 1:
            QMessageBox.information(self, "Cannot Remove", "At least one garment page is required.")
            return

        saved_data  = card.get_data()
        saved_index = self._cards.index(card)

        self._cards.remove(card)
        self.cards_layout.removeWidget(card)
        card.deleteLater()
        self._renumber_cards()
        self._update_status()

        self._show_undo_toast(f"Garment {saved_index + 1} removed", saved_data, saved_index)

    def _renumber_cards(self):
        for i, card in enumerate(self._cards, 1):
            card.update_index(i)

    def _update_status(self):
        n = len(self._cards)
        self.status_label.setText(f"{n} garment{'s' if n != 1 else ''} • Ready to generate")

    def _show_undo_toast(self, message: str, data: dict, index: int):
        if self._toast:
            self._toast.hide()
            self._toast.deleteLater()

        self._toast = _Toast(message, self)
        self._toast.undo_clicked.connect(lambda: self._undo_remove(data, index))
        self._toast.reposition(self.width(), self.height())
        self._toast.show()
        self._toast.raise_()

    def _undo_remove(self, data: dict, index: int):
        # insert a fresh card at the original position with the saved data
        card = GarmentPageCard(index + 1)
        card.remove_requested.connect(self._remove_card)
        card.style_input.setText(data.get("style", ""))
        card.fabric_input.setText(data.get("fabric", ""))
        card.gsm_input.setText(data.get("gsm", ""))
        for view, path in data.get("images", {}).items():
            if path and Path(path).exists() and view in card.boxes:
                card.boxes[view]._accept(path)

        self._cards.insert(index, card)
        self.cards_layout.insertWidget(index, card)
        self._renumber_cards()
        self._update_status()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._toast and self._toast.isVisible():
            self._toast.reposition(self.width(), self.height())

    def _batch_import(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Garment Images")
        if not folder:
            return

        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        groups: dict[str, dict[str, str]] = {}

        for f in sorted(Path(folder).iterdir()):
            if f.suffix.lower() not in valid_exts:
                continue
            stem = f.stem.lower()
            for view in ("front", "back", "design"):
                if stem.endswith(f"_{view}") or stem.endswith(f"-{view}"):
                    prefix = stem[: -(len(view) + 1)]
                    groups.setdefault(prefix, {})[view] = str(f)
                    break

        if not groups:
            QMessageBox.information(
                self, "No Images Found",
                "No files matching *_front.*, *_back.*, or *_design.* were found in that folder."
            )
            return

        # clear existing cards only if none of them have images yet
        if all(c.is_empty() for c in self._cards):
            for card in self._cards[:]:
                self.cards_layout.removeWidget(card)
                card.deleteLater()
            self._cards.clear()

        for views in groups.values():
            card = GarmentPageCard(len(self._cards) + 1)
            card.remove_requested.connect(self._remove_card)
            for view, path in views.items():
                if view in card.boxes:
                    card.boxes[view]._accept(path)
            self._cards.append(card)
            self.cards_layout.addWidget(card)

        self._update_status()

    def _on_generate(self):
        pages = [c.get_data() for c in self._cards]

        if all(not p["images"] for p in pages):
            QMessageBox.warning(self, "No Images",
                                "Please upload at least one garment image before generating.")
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("Generating…")
        self.status_label.setText("Processing images…")

        title = self.title_input.text().strip()
        self._worker = CatalogWorker(pages, title)
        self._worker.finished.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, pdf_path: str, layout_paths: list):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Generate PDF")
        self.status_label.setText("✓ Catalog generated!")

        thumb_path = layout_paths[0] if layout_paths else ""
        self.catalog_generated.emit(pdf_path, thumb_path)

        dlg = _SuccessDialog(pdf_path, layout_paths, self)
        dlg.exec()

    def _on_failure(self, error: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Generate PDF")
        self.status_label.setText("⚠ Generation failed")
        QMessageBox.critical(self, "Generation Failed",
                             f"Could not generate catalog:\n\n{error}")

    @staticmethod
    def _gen_btn_style():
        return f"""
            QPushButton {{
                background: {NAVY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 13px;
                font-weight: 700;
                min-width: 160px;
            }}
            QPushButton:hover {{ background: {NAVY_LITE}; }}
            QPushButton:disabled {{ background: #94A3B8; }}
        """


class _Toast(QFrame):
    undo_clicked = pyqtSignal()

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QFrame#toast {
                background: #1E1E2E;
                border-radius: 8px;
            }
        """)
        self.setFixedHeight(44)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(12)

        msg = QLabel(message)
        msg.setStyleSheet("color: #E2E8F0; font-size: 13px; background: transparent;")

        undo_btn = QPushButton("Undo")
        undo_btn.setFlat(True)
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.setStyleSheet(f"""
            QPushButton {{
                color: {ACCENT};
                background: transparent;
                border: none;
                font-weight: 700;
                font-size: 13px;
                padding: 0 4px;
            }}
            QPushButton:hover {{ color: {NAVY_LITE}; }}
        """)
        undo_btn.clicked.connect(self._on_undo)

        lay.addWidget(msg)
        lay.addStretch()
        lay.addWidget(undo_btn)

        # auto-dismiss after 5 seconds
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._timer.start(5000)

    def _on_undo(self):
        self._timer.stop()
        self.undo_clicked.emit()
        self.hide()

    def reposition(self, parent_w: int, parent_h: int):
        w = min(360, parent_w - 60)
        self.setFixedWidth(w)
        x = (parent_w - w) // 2
        y = parent_h - 44 - 72  # sit just above the bottom bar (64px) + 8px gap
        self.move(x, y)
        self.raise_()


class _PreviewDialog(QDialog):
    def __init__(self, layout_paths: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catalog Preview")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        self.setStyleSheet(f"background: {BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        for path in layout_paths:
            pix = QPixmap(path)
            if pix.isNull():
                continue
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setPixmap(pix.scaled(
                900, 580,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            lbl.setStyleSheet(
                f"background: {WHITE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px;"
            )
            content_layout.addWidget(lbl)

        content_layout.addStretch()
        scroll.setWidget(content)

        bottom = QFrame()
        bottom.setFixedHeight(56)
        bottom.setStyleSheet(f"background: {WHITE}; border-top: 1px solid {BORDER};")
        bottom_lay = QHBoxLayout(bottom)
        bottom_lay.setContentsMargins(16, 0, 16, 0)

        page_info = QLabel(f"{len(layout_paths)} page{'s' if len(layout_paths) != 1 else ''}")
        page_info.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {NAVY};
                color: white;
                border-radius: 7px;
                padding: 0 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {NAVY_LITE}; }}
        """)
        close_btn.clicked.connect(self.close)

        bottom_lay.addWidget(page_info)
        bottom_lay.addStretch()
        bottom_lay.addWidget(close_btn)

        root.addWidget(scroll, 1)
        root.addWidget(bottom)


class _SuccessDialog(QMessageBox):
    def __init__(self, pdf_path: str, layout_paths: list[str], parent=None):
        super().__init__(parent)
        self._layout_paths = layout_paths
        self.setWindowTitle("Catalog Ready")
        self.setIcon(QMessageBox.Icon.NoIcon)
        self.setText(
            f"<b style='font-size:15px;'>✅ Catalog generated!</b><br><br>"
            f"<span style='color:#64748B;font-size:12px;'>{pdf_path}</span>"
        )
        self.setStandardButtons(QMessageBox.StandardButton.Ok)

        open_btn    = self.addButton("Open PDF",       QMessageBox.ButtonRole.ActionRole)
        show_btn    = self.addButton("Show in Folder", QMessageBox.ButtonRole.ActionRole)
        preview_btn = self.addButton("Preview Pages",  QMessageBox.ButtonRole.ActionRole)

        open_btn.clicked.connect(lambda: self._open(pdf_path))
        show_btn.clicked.connect(lambda: self._reveal(pdf_path))
        preview_btn.clicked.connect(self._open_preview)

        self.setStyleSheet(f"""
            QMessageBox {{ background: {WHITE}; }}
            QPushButton {{
                background: {NAVY};
                color: white;
                border-radius: 7px;
                padding: 6px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {NAVY_LITE}; }}
        """)

    def _open_preview(self):
        dlg = _PreviewDialog(self._layout_paths, self)
        dlg.exec()

    @staticmethod
    def _open(path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(None, "Error", str(e))

    @staticmethod
    def _reveal(path):
        folder = str(Path(path).parent)
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", folder])
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(None, "Error", str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Catalog Studio")
        logo = APP_ROOT / "app_logo.png"
        if logo.exists():
            self.setWindowIcon(QIcon(str(logo)))
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar  = Sidebar()
        self.workarea = WorkArea()
        self.workarea.catalog_generated.connect(self.sidebar.add_catalog)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.workarea, 1)

        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

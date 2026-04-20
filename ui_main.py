import os
import subprocess
import sys
import traceback
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QScrollArea,
    QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from widgets import (
    GarmentPageCard, CatalogHistoryItem,
    BG, NAVY, NAVY_LITE, ACCENT, BORDER, TEXT, SUBTEXT, WHITE,
)
from backend_wrapper import generate_catalog

OUTPUT_DIR = Path(__file__).parent.resolve() / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class CatalogWorker(QThread):
    finished = pyqtSignal(str)
    failed   = pyqtSignal(str)

    def __init__(self, pages: list[dict]):
        super().__init__()
        self.pages = pages

    def run(self):
        try:
            pdf_path = generate_catalog(self.pages)
            self.finished.emit(pdf_path)
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
        brand_lay.setContentsMargins(20, 0, 20, 0)

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
            "color: #A8C4E8; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
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
            self._add_item(str(pdf))

    def add_catalog(self, pdf_path: str):
        self.empty_label.hide()
        self._add_item(pdf_path, prepend=True)

    def _add_item(self, pdf_path: str, prepend: bool = False):
        item = CatalogHistoryItem(pdf_path)
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
    catalog_generated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")
        self._cards: list[GarmentPageCard] = []
        self._worker = None
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

        self.gen_btn = QPushButton("  ⬇  Generate PDF")
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

        self.add_page_btn = QPushButton("＋  Add Garment")
        self.add_page_btn.setFixedHeight(38)
        self.add_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_page_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1.5px solid {ACCENT};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #EFF6FF;
            }}
        """)
        self.add_page_btn.clicked.connect(self._add_card)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")

        bottom_lay.addWidget(self.add_page_btn)
        bottom_lay.addStretch()
        bottom_lay.addWidget(self.status_label)

        root.addWidget(topbar)
        root.addWidget(self.scroll, 1)
        root.addWidget(bottom)

        self._add_card()

    def _add_card(self):
        card = GarmentPageCard(len(self._cards) + 1)
        card.remove_requested.connect(self._remove_card)
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
        self._cards.remove(card)
        self.cards_layout.removeWidget(card)
        card.deleteLater()
        self._renumber_cards()
        self._update_status()

    def _renumber_cards(self):
        for i, card in enumerate(self._cards, 1):
            card.update_index(i)

    def _update_status(self):
        n = len(self._cards)
        self.status_label.setText(f"{n} garment{'s' if n != 1 else ''} • Ready to generate")

    def _on_generate(self):
        pages = [c.get_data() for c in self._cards]

        if all(not p["images"] for p in pages):
            QMessageBox.warning(self, "No Images",
                                "Please upload at least one garment image before generating.")
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("  ⏳  Generating…")
        self.status_label.setText("Processing images…")

        self._worker = CatalogWorker(pages)
        self._worker.finished.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, pdf_path: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("  ⬇  Generate PDF")
        self.status_label.setText("✓ Catalog generated!")
        self.catalog_generated.emit(pdf_path)

        dlg = _SuccessDialog(pdf_path, self)
        dlg.exec()

    def _on_failure(self, error: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("  ⬇  Generate PDF")
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


class _SuccessDialog(QMessageBox):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self._path = pdf_path
        self.setWindowTitle("Catalog Ready")
        self.setIcon(QMessageBox.Icon.NoIcon)
        self.setText(
            f"<b style='font-size:15px;'>✅ Catalog generated!</b><br><br>"
            f"<span style='color:#64748B;font-size:12px;'>{pdf_path}</span>"
        )
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        open_btn = self.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
        show_btn = self.addButton("Show in Folder", QMessageBox.ButtonRole.ActionRole)

        open_btn.clicked.connect(lambda: self._open(pdf_path))
        show_btn.clicked.connect(lambda: self._reveal(pdf_path))

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
        self.setWindowTitle("Garment Catalog Studio")
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

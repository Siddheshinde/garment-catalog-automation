import sys
import ctypes
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from ui_main import MainWindow

APP_ROOT = Path(__file__).parent.resolve()

# tell Windows this is its own app identity so the taskbar uses our icon
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CatalogStudio.App.1")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Catalog Studio")
    app.setOrganizationName("CatalogStudio")
    app.setFont(QFont("Segoe UI", 10))

    logo = APP_ROOT / "app_logo.png"
    if logo.exists():
        app.setWindowIcon(QIcon(str(logo)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

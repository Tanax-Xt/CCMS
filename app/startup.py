import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo
from PyQt6.QtWidgets import QApplication

from app.db import ENGINE
from app.db.models import BaseModel
from app.ui.widgets.windows import MainWindow


def run() -> int:
    """
    Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """
    BaseModel.metadata.create_all(ENGINE)

    app: QApplication = QApplication(sys.argv)
    app.setWindowIcon(QIcon("app/ui/resourses/favicon.ico"))

    translator = QTranslator(app)
    if translator.load(
        QLocale(QLocale.Language.Russian),
        "qtbase",
        "_",
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    ):
        app.installTranslator(translator)

    window: MainWindow = MainWindow()
    window.show()

    return sys.exit(app.exec())

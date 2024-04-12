from PyQt6.QtWidgets import QWidget, QMessageBox


def validationError(parent: QWidget, message):
    QMessageBox.critical(parent, "Ошибка проверки", message)


def confirm(parent: QWidget | None, message) -> bool:
    return QMessageBox.question(parent, "Подтверждение", message) == QMessageBox.StandardButton.Yes

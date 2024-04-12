import csv
from os.path import expanduser

from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtWidgets import QWidget, QMessageBox, QFileDialog

def export(model: QAbstractTableModel, parent: QWidget, vert=False) -> None:
    PATH, EXTENSION = QFileDialog.getSaveFileName(
        parent, "Укажите путь", expanduser("~"), "*.csv"
    )
    if not EXTENSION:
        return

    if vert:
        headers: list[str] = [""]
    else:
        headers: list[str] = []

    for col in range(model.columnCount()):
        headers.append(model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))

    with open(PATH, "w", encoding="UTF-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for rowNumber in range(model.rowCount()):
            fields = [
                model.data(
                    model.index(rowNumber, columnNumber), Qt.ItemDataRole.DisplayRole
                )
                for columnNumber in range(model.columnCount())
            ]
            if vert:
                h = model.headerData(rowNumber, Qt.Orientation.Vertical, role=Qt.ItemDataRole.DisplayRole)
                fields.insert(0, h)
            writer.writerow(fields)

    QMessageBox.information(parent, "Экспорт завершён", f"Файл был успешно сохранён в '{PATH}'.")
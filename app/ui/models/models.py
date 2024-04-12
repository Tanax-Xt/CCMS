from typing import Any, Callable, Dict, Set, TypeVar, Generic

from PyQt6.QtCore import (
    QObject,
    Qt,
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox
from sqlmodel import Session

from app.db import ENGINE
from app.db.models import BaseModel, Club, Reservation, Scope, UniqueNamedModel, Event, Assignment, Weekday
from app.ui.widgets.schedule import WEEKDAY_NAMES

TBaseNamedModel = TypeVar("TBaseNamedModel", bound=UniqueNamedModel)
TModel = TypeVar("TModel", bound=BaseModel)

DATE_FORMAT = "%d.%m.%Y %H:%M"

SCOPES = {
    Scope.ENTERTAINMENT: "Развлечение",
    Scope.ENLIGHTENMENT: "Просвещение",
}

STATES = {
    Assignment.State.DRAFT: "Черновик",
    Assignment.State.ACTIVE: "Активно",
    Assignment.State.COMPLETED: "Выполнено"
}


class TypeListModel(Generic[TBaseNamedModel], QAbstractListModel):
    def __init__(
        self, data: Set[TBaseNamedModel], parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._data = data

    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self._data)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._data[index.row()].name

    def insertRow(
        self, row: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        self.beginInsertRows(parent, row, row)

        name = self._generateUniqueName()

        with Session(ENGINE) as session:
            newObj: TBaseNamedModel = self._getGenericType()(name=name, **kwargs)
            session.add(newObj)
            session.commit()
            session.refresh(newObj)

        self._data.append(newObj)

        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)

        item = self._data[row]

        if (
            self._showObjectDeletionConfirmation(item.name)
            != QMessageBox.StandardButton.Ok
        ):
            return False

        self._data.remove(item)

        with Session(ENGINE) as session:
            session.delete(item)
            session.commit()

        self.endRemoveRows()
        return True

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            return self.editData(index, value)

    def editData(self, index: QModelIndex, value: Any) -> bool:
        item = self._data[index.row()]

        if item.name == value:
            return False

        if value == "" or self.isUniqueNameConstraintFailed(value):
            self._showUniqueNameConstraintWarning(value)
            return False

        with Session(ENGINE) as session:
            obj = session.get(self._getGenericType(), item.id)
            obj.name = value
            session.add(obj)
            session.commit()
            session.refresh(obj)

        item.name = value

        self.dataChanged.emit(index, index)
        return True

    def flags(self, _: QModelIndex) -> Qt.ItemFlag:
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

    def isUniqueNameConstraintFailed(self, name: str) -> bool:
        return any(item.name == name for item in self._data)

    def _generateUniqueName(self):
        i = 0
        row_count = self.rowCount()
        name = f"Объект ({row_count})"
        while self.isUniqueNameConstraintFailed(name):
            name = f"Объект ({row_count + i})"
            i += 1
        return name

    def _showUniqueNameConstraintWarning(self, name: str) -> None:
        QMessageBox.critical(
            self.parent(), "Ошибка", f"Объект названием '{name}' уже был создан ранее."
        )

    def _showObjectDeletionConfirmation(self, name: str) -> bool:
        return QMessageBox.warning(
            self.parent(),
            "Подтверждение удаления объекта",
            f"Вы действительно хотите удалить '{name}'?",
            defaultButton=QMessageBox.StandardButton.Close,
        )

    def _getGenericType(self) -> TBaseNamedModel:
        return self.__orig_class__.__args__[0]


class BaseTableModel(Generic[TModel], QAbstractTableModel):
    GENERATORS: Dict[str, Callable[[TModel], Any]] | None = None

    def __init__(self, data: Set[TModel], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = data
        self._headers = list(self.GENERATORS.keys())

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._headers[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, _: QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, _: QModelIndex = ...) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            item = self._data[index.row()]
            with Session(ENGINE) as session:
                session.add(item)
                return list(self.GENERATORS.values())[index.column()](item)

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        item = self._data[row]
        self._data.remove(item)
        self.endRemoveRows()
        return True


class ScheduleTableModel(QAbstractTableModel):
    DATE_FMT = "%H:%M"

    def __init__(self, data: list[Club], parent: QObject | None = None) -> None:
        self._data = data
        super().__init__(parent)
        
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(WEEKDAY_NAMES)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return super().headerData(section, orientation, role)

        if orientation == Qt.Orientation.Vertical:
            return self._data[section].title
        return list(WEEKDAY_NAMES.values())[section]
    
    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return
        weekday = Weekday(index.column() + 1)
        with Session(ENGINE) as session:
            club: Club | None = session.get(Club, self._data[index.row()].id)
            if club is None:
                return
            schedule_day = next((d for d in club.days if d.weekday == weekday), None)
            if not schedule_day:
                return
            return f"{schedule_day.start_at.strftime(self.DATE_FMT)} - {schedule_day.end_at.strftime(self.DATE_FMT)} - {club.location.name if club.location else None} - {club.teacher.name if club.teacher else None}" 


class EventTableModel(BaseTableModel[Event]):
    GENERATORS = {
        "Заголовок": lambda e: e.title,
        "Пространство": lambda e: SCOPES[e.scope],
        "Разновидность": lambda e: e.type.name if e.type else None,
        "Помещение": lambda e: str.join(", ", (r.location.name for r in e.reservations)) if any(e.reservations) else None,
        "Дата начала": lambda e: e.start_at.strftime(DATE_FORMAT),
        "Дата создания": lambda e: e.created_at.strftime(DATE_FORMAT),
        "Описание": lambda e: e.description,
    }


class AssignmentTableModel(BaseTableModel[Assignment]):
    GENERATORS = {
        "Помещение": lambda a: a.location.name if a.location else None,
        "Разновидность": lambda a: a.type.name,
        "Мероприятие": lambda a: a.event.title if a.event else None,
        "Статус": lambda a: STATES[a.state],
        "Дедлайн": lambda a: a.deadline.strftime(DATE_FORMAT),
        "Дата создания": lambda a: a.created_at.strftime(DATE_FORMAT),
        "Описание": lambda a: a.description,
    }

    STATUS_COLORS = {
        Assignment.State.DRAFT: None,
        Assignment.State.ACTIVE: QColor("lightpink"),
        Assignment.State.COMPLETED: QColor("lightgray"),
    }

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role != Qt.ItemDataRole.BackgroundRole:
            return super().data(index, role)

        assignment: Assignment = self._data[index.row()]
        return self.STATUS_COLORS[assignment.state]


class ReservaionTableModel(BaseTableModel[Reservation]):
    GENERATORS = {
        "Помещение": lambda r: r.location.name if r.location else None,
        "Зоны": lambda r: str.join(", ", (a.name for a in r.areas)) if any(r.areas) else None,
        "Мероприятие": lambda r: r.event.title if r.event else None,
        "Дата начала": lambda r: r.start_at.strftime(DATE_FORMAT),
        "Дата конца": lambda r: r.end_at.strftime(DATE_FORMAT),
        "Комментарий": lambda r: r.comment,
        "Дата создания": lambda r: r.created_at.strftime(DATE_FORMAT),
    }


class ClubTableModel(BaseTableModel[Club]):
    GENERATORS = {
        "Заголовок": lambda c: c.title,
        "Помещение": lambda c: c.location.name if c.location else None,
        "Преподаватель": lambda c: c.teacher.name if c.teacher else None,
        "Вид": lambda c: c.type.name if c.type else None,
        "Старт": lambda c: c.start_at.strftime(DATE_FORMAT),
        "Расписание": lambda c: f"{len(c.days)} раз(а) в неделю",
        "Дата создания": lambda c: c.created_at.strftime(DATE_FORMAT),
    }


__all__ = [
    "BaseTableModel",
    "TypeListModel",
    "EventTableModel",
    "AssignmentTableModel",
    "ReservaionTableModel",
    "ClubTableModel",
]

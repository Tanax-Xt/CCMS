from abc import ABC, abstractmethod
from sqlalchemy import BinaryExpression
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Session, select, and_

from PyQt6 import QtWidgets, QtCore

from app.db import ENGINE
from app.ui.widgets.dialogs.ext import TypeManagerDialog
from app.ui.widgets.mixins import WidgetMixin

__all__ = ["FilterBox", "ComboboxFilter", "DateTimeRangeFilter"]


class Filter(ABC):
    def __init__(self, label_text, statement: InstrumentedAttribute) -> None:
        self._label_text = label_text
        self._statement = statement

    @abstractmethod
    def setup(self, form: QtWidgets.QFormLayout) -> None:
        ...

    @abstractmethod
    def apply(self) -> None:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...
    
    def refresh(self) -> None:
        pass


class FilterBox(QtWidgets.QGroupBox, WidgetMixin):
    ui_path = "app/ui/assets/filter.ui"
    title = None
    where: BinaryExpression | None = None

    def __init__(self, filters: tuple[Filter], table, parent) -> None:
        self._filters = filters
        self._table = table
        super().__init__(parent)

    def setup_ui(self) -> None:
        self.resetButton.clicked.connect(self.reset)
        self.applyButton.clicked.connect(self.apply)

        for filter in self._filters:
            filter.setup(self.formLayout)

    def reset(self):
        self.where = None
        for filter in self._filters:
            filter.reset()
        self._table.refresh(filter=False)

    def apply(self):
        statements = []
        for filter in self._filters:
            statement = filter.apply()
            if statement is not None:
                statements.append(statement)
        if len(statements) != 0:
            self.where = and_(*statements)
        self._table.refresh(filter=False)
        
    def refresh(self):
        for filter in self._filters:
            filter.refresh()


class TextFilter(Filter):
    def setup(self, form: QtWidgets.QFormLayout) -> None:
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setPlaceholderText("Начните писать…")
        self.lineEdit.setClearButtonEnabled(True)
        form.addRow(QtWidgets.QLabel(self._label_text), self.lineEdit)
        
    def apply(self):
        return self._statement.contains(self.lineEdit.text())
    
    def reset(self) -> None:
        self.lineEdit.clear()


class ComboboxFilter(Filter):
    @property
    def data(self):
        with Session(ENGINE) as session:
            return session.exec(select(self._statement)).all()
        
    def __init__(self, label_text, statement: InstrumentedAttribute, is_maximize: bool = False, _t = TypeManagerDialog) -> None:
        self._is_maximize = is_maximize
        self._t = _t
        super().__init__(label_text, statement)

    def get_comparer(self, text):
        return text
    
    def setup(self, form: QtWidgets.QFormLayout) -> None:
        self.combobox = QtWidgets.QComboBox()
        self.combobox.setEditable(True)
        self.refresh()
        self.combobox.lineEdit().setPlaceholderText("Не выбрано")
        self.combobox.lineEdit().setClearButtonEnabled(True)
        self.combobox.completer().setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.combobox.completer().setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.combobox.view().setMinimumWidth(self.combobox.view().sizeHintForColumn(0))
        self.combobox.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        if self._is_maximize:
            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(self.combobox)
            self.maximize = QtWidgets.QToolButton()
            self.maximize.setText("…")
            if self._t == TypeManagerDialog:
                self.mng = self._t(self._statement.parent.class_)
            else:
                self.mng = self._t()
            self.maximize.clicked.connect(self.mng.exec)
            self.mng.accepted.connect(self.refresh)
            hbox.addWidget(self.maximize)
            form.addRow(QtWidgets.QLabel(self._label_text), hbox)
        else:
            form.addRow(QtWidgets.QLabel(self._label_text), self.combobox)

    def apply(self):
        text = self.combobox.currentText()
        if text:
            return self._statement == self.get_comparer(text)

    def reset(self) -> None:
        self.combobox.setCurrentIndex(-1)
        
    def refresh(self) -> None:
        self.combobox.clear()
        self.combobox.addItems(self.data)
        self.combobox.lineEdit().clear()
        self.combobox.lineEdit().setPlaceholderText("Не выбрано")


class EnumFilter(ComboboxFilter):
    def __init__(self, label_text, statement: InstrumentedAttribute, mapping: dict) -> None:
        self.names = mapping
        super().__init__(label_text, statement)
        
    @property
    def data(self):
        return self.names.values()
    
    def get_comparer(self, text):
        return next(key for key, value in self.names.items() if value == text)


MINIMUM_DATE_TIME = QtCore.QDateTime(2000, 1, 1, 0, 0)

class DateTimeRangeFilter(Filter):
    def __init__(self, label_text, statement: InstrumentedAttribute, enable_shortcuts: bool = False) -> None:
        self.enable_shortcuts = enable_shortcuts
        super().__init__(label_text, statement)
    
    def setup(self, form: QtWidgets.QFormLayout) -> None:
        line = QtWidgets.QFrame()

        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        form.addRow(line)
        form.addRow(QtWidgets.QLabel(self._label_text))

        self.fr = QtWidgets.QDateTimeEdit()
        self.fr.setCalendarPopup(True)
        self.fr.setMinimumDateTime(MINIMUM_DATE_TIME)
        
        form.addRow(QtWidgets.QLabel("От:"), self.fr)

        self.to = QtWidgets.QDateTimeEdit()
        self.to.setCalendarPopup(True)
        self.to.setMinimumDateTime(MINIMUM_DATE_TIME)
        form.addRow(QtWidgets.QLabel("До:"), self.to)
        
        if self.enable_shortcuts:
            self._add_shortcuts(form)
        self.reset()

    def apply(self):
        fr_dt = self.fr.dateTime().toPyDateTime()
        to_dt = self.to.dateTime().toPyDateTime()

        conditions = []

        if fr_dt != self.fr.minimumDateTime().toPyDateTime():
            conditions.append(self._statement > fr_dt)

        if to_dt != self.to.minimumDateTime().toPyDateTime():
            conditions.append(self._statement < to_dt)

        return and_(*conditions) if conditions else None

    def reset(self) -> None:
        self.fr.setDateTime(self.fr.minimumDateTime())
        self.to.setDateTime(self.to.minimumDateTime())

        self.fr.setSpecialValueText("Не выбрано")
        self.to.setSpecialValueText("Не выбрано")
        
    def _add_shortcuts(self, form: QtWidgets.QFormLayout):
        self.shortcuts = {
            "Завтра": 1,
            "Послезавтра": 2,
            "Через 3 дня": 3,
            "Через 7 дней": 7,
            "Через 14 дней": 14,
            "Через 30 дней": 30,
        }
        
        grid = QtWidgets.QGridLayout()
        
        for i, (text, days) in enumerate(self.shortcuts.items()):
            btn = QtWidgets.QToolButton()
            btn.setText(text)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _, days=days: self.to.setDate(QtCore.QDate.currentDate().addDays(days)))
            
            col = i % 3
            row = i // 3 + i - col
            grid.addWidget(btn, row, col)
            grid.setRowStretch(row, 1)
            grid.setColumnStretch(col, 1)
            
        form.addRow(grid)

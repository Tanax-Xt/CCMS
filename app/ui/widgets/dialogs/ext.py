from sqlmodel import Session, select

from PyQt6 import uic, QtWidgets

from app.db import ENGINE
from app.db.models import (
    Area,
    BaseModel,
    Location,
)
from app.ui.models import TypeListModel
from app.ui.widgets.alerts import validationError
from app.ui.widgets.mixins import WidgetMixin
        

class TypeManagerDialog(QtWidgets.QDialog):
    def __init__(self, _type, parent = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/assets/dialogs/type-manager.ui", self)

        with Session(ENGINE) as session:
            data = session.exec(select(_type)).all()

        self.listViewModel = TypeListModel[_type](data, self)
        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(
            lambda: self.delButton.setDisabled(False)
        )

        self.addButton.clicked.connect(self.onAddButtonClicked)
        self.delButton.clicked.connect(self.onDelButtonClicked)

    def onAddButtonClicked(self, **kwargs) -> None:
        self.listViewModel.insertRow(-1, **kwargs)
        index = self.listViewModel.index(self.listViewModel.rowCount() - 1, 0)
        self.listView.edit(index)
        self.listView.setCurrentIndex(index)

    def onDelButtonClicked(self) -> None:
        currentRowIndex = self.listView.currentIndex().row()
        self.listViewModel.removeRow(currentRowIndex)


class AreaManagerDialog(TypeManagerDialog):
    def __init__(self, parent = None) -> None:
        super().__init__(Area, parent)
        self.combobox = QtWidgets.QComboBox()
        self.combobox.currentTextChanged.connect(self.updateModel)

        with Session(ENGINE) as session:
            self.names = session.exec(select(Location.name)).all()

        self.combobox.addItems(name for name in self.names)
        self.verticalLayout_4.addWidget(self.combobox)

    def exec(self) -> int:
        if self.names:
            return super().exec()
        validationError(self, "Вы должны создать хотя бы одно помещение!")
        return False

    def updateModel(self, name: str):
        with Session(ENGINE) as session:
            self.location = session.exec(select(Location).where(Location.name == name)).first()
            self.listViewModel = TypeListModel[Area](self.location.areas, self)

        self.listView.setModel(self.listViewModel)

        self.delButton.setDisabled(True)
        self.listView.selectionModel().selectionChanged.connect(
            lambda: self.delButton.setDisabled(not(bool(self.listView.selectedIndexes())))
        )

    def onAddButtonClicked(self) -> None:
        super().onAddButtonClicked(location_id=self.location.id)


class DialogView(QtWidgets.QDialog, WidgetMixin):
    model: BaseModel

    def __init__(self, obj=None, parent: QtWidgets.QWidget | None = None) -> None:
        self.obj = obj
        super().__init__(parent)

    @property
    def obj(self):
        return self._obj or self.model()

    @obj.setter
    def obj(self, value) -> None:
        self._obj = value

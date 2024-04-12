from enum import StrEnum, auto
from sqlmodel import Session, select, exists

from PyQt6 import QtWidgets, QtCore, uic

from app.db import ENGINE
from app.db.models import Area, Event, Location, Reservation


class Fields(StrEnum):
    START_AT = auto()
    END_AT = auto()
    PLACE_ID = auto()
    AREA_IDS = auto()
    COMMENT = auto()


class WelcomePage(QtWidgets.QWizardPage):    
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/assets/wizards/welcome-page.ui", self)
        self.registerField(Fields.START_AT, self.startDateTimeEdit)
        self.registerField(Fields.END_AT, self.endDateTimeEdit)

    def initializePage(self) -> None:
        self.endDateTimeEdit.setMinimumDateTime(QtCore.QDateTime(self.wizard()._event.start_at))
        self.startDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())
    
    def validatePage(self) -> bool:
        if self.startDateTimeEdit.dateTime() >= self.endDateTimeEdit.dateTime():
            QtWidgets.QMessageBox.critical(self, "Ошибка валидации!", "Время начала должно быть больше вермени конца!")
            return False

        self.setField(Fields.START_AT, self.startDateTimeEdit.dateTime())
        self.setField(Fields.END_AT, self.endDateTimeEdit.dateTime())
        return super().validatePage()


class ResultsPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/assets/wizards/results-page.ui", self)
        
        # self.registerField(Fields.PLACE_ID, self.listWidget)
        spin = QtWidgets.QSpinBox(self)
        spin.setVisible(False)
        self.registerField(Fields.PLACE_ID, spin)
        self.listWidget.itemSelectionChanged.connect(lambda: self.completeChanged.emit())

    def initializePage(self) -> None:
        self.listWidget.clear()

        start_at = self.field(Fields.START_AT).toPyDateTime()
        end_at = self.field(Fields.END_AT).toPyDateTime()
        
        # Так писать нельзя, позже отрефакторю! Но оно работает :)
        with Session(ENGINE) as session:
            locations = session.exec(select(Location)).all()
            free = []
            for location in locations:

                # Полностью пустое
                if not(any(location.areas) or any(location.reservations)):
                    free.append(location)
                    continue

                # Бронирование не пересекается
                if (any(reservation.start_at < reservation.end_at < start_at < end_at for reservation in location.reservations)
                    or any(start_at < end_at < reservation.start_at < reservation.end_at for reservation in location.reservations)):

                    # Нет зон
                    if not(any(location.areas)):
                        free.append(location)
                        continue
                    
                    for area in location.areas:
                        
                        # Полностью пустое
                        if not any(area.reservations):
                            free.append(location)
                            break
                        
                        # Бронирование не пересекается
                        if (any(reservation.start_at < reservation.end_at < start_at < end_at for reservation in area.reservations)
                            or any(start_at < end_at < reservation.start_at < reservation.end_at for reservation in area.reservations)):
                            free.append(location)
                            break

                    continue

                for area in location.areas:
                        
                    # Полностью пустое
                    if not any(area.reservations):
                        free.append(location)
                        break
                    
                    # Бронирование не пересекается
                    if (any(reservation.start_at < reservation.end_at < start_at < end_at for reservation in area.reservations)
                        or any(start_at < end_at < reservation.start_at < reservation.end_at for reservation in area.reservations)):
                        free.append(location)
                        break

            names = list(location.name for location in free)

        self.listWidget.addItems(names)

        # print(start_at)
        # end_at = self.field("end_at").toPyDateTime().strftime("%d.%m.%Y %H:%M")
        # title = f"Ниже перечислены варианты бронирования на период с {start_at} до {end_at}:"
        # self.setSubTitle(title)

    def isComplete(self) -> bool:
        return bool(self.listWidget.selectedIndexes())
        
    def validatePage(self) -> bool:        
        with Session(ENGINE) as session:
            name = self.listWidget.currentItem().data(QtCore.Qt.ItemDataRole.DisplayRole)
            location_id = session.exec(select(Location.id).where(Location.name == name)).first()
            self.setField(Fields.PLACE_ID, location_id)

        return super().validatePage()


class AreasPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/assets/wizards/areas-page.ui", self)
        self.location = None
        lst = QtWidgets.QListWidget(self)
        lst.setVisible(False)
        self.registerField(Fields.AREA_IDS, lst, "selectedItems")
        self.listWidget.itemChanged.connect(lambda: self.completeChanged.emit())
        self.reserveAllCheckBox.toggled.connect(self.toggleAll)
        
    def toggleAll(self, is_checked: bool):
        state = QtCore.Qt.CheckState.Checked if is_checked else QtCore.Qt.CheckState.Unchecked
        
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if QtCore.Qt.ItemFlag.ItemIsEnabled in item.flags():
                item.setCheckState(state)
            self.listWidget.insertItem(i, item)

    def initializePage(self) -> None:
        self.listWidget.clear()
        self.reserveAllCheckBox.setChecked(False)

        start_at = self.field(Fields.START_AT).toPyDateTime()
        end_at = self.field(Fields.END_AT).toPyDateTime()
        location_id: int = self.field(Fields.PLACE_ID)

        with Session(ENGINE) as session:
            self.location = session.get(Location, location_id)
            for area in self.location.areas:
                item = QtWidgets.QListWidgetItem(area.name)
                
                is_busy = True
                
                # Полностью пустое
                if not any(area.reservations):
                    is_busy = False
    
                # Бронирование не пересекается
                if (any(reservation.start_at < reservation.end_at < start_at < end_at for reservation in area.reservations)
                    or any(start_at < end_at < reservation.start_at < reservation.end_at for reservation in area.reservations)):
                    is_busy = False
                
                flags = QtCore.Qt.ItemFlag.NoItemFlags if is_busy else QtCore.Qt.ItemFlag.ItemIsEnabled

                item.setFlags(flags | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
                self.listWidget.addItem(item)
        return super().initializePage()
    
    def isComplete(self) -> bool:
        return any(self.listWidget.item(i).checkState() == QtCore.Qt.CheckState.Checked for i in range(self.listWidget.count()))
    
    def validatePage(self) -> bool:
        names = frozenset(
            self.listWidget.item(i).data(QtCore.Qt.ItemDataRole.DisplayRole) 
            for i in range(self.listWidget.count()) 
            if self.listWidget.item(i).checkState() == QtCore.Qt.CheckState.Checked
        )
        ids = frozenset(area.id for area in self.location.areas if area.name in names)
        self.setField(Fields.AREA_IDS, ids)

        return super().validatePage()


class FinalPage(QtWidgets.QWizardPage):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        uic.loadUi("app/ui/assets/wizards/final-page.ui", self)
        self.registerField(Fields.COMMENT, self.commentTextEdit)
        
    def validatePage(self) -> bool:
        self.setField(Fields.COMMENT, self.commentTextEdit.toPlainText())
        return super().validatePage()


class ReservationWizard(QtWidgets.QWizard):
    def __init__(self, event: Event, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._event = event

        self.setWindowTitle("Мастер бронирования помещений")

        self.welcomePage = WelcomePage()
        self.resultsPage = ResultsPage()
        self.areasPage = AreasPage()
        self.finalPage = FinalPage()

        self.addPage(self.welcomePage)
        self.addPage(self.resultsPage)
        self.addPage(self.areasPage)
        self.addPage(self.finalPage)

        self.button(QtWidgets.QWizard.WizardButton.FinishButton).clicked.connect(self.createReservation)

    def nextId(self) -> int:
        if self.currentPage() != self.resultsPage:
            return super().nextId()

        location_id: int = self.field(Fields.PLACE_ID)
        with Session(ENGINE) as session:
            (ret, ), = session.query(exists().where(Area.location_id == location_id))
        
        if ret:
            return super().nextId()
        return self.currentId() + 2

    def createReservation(self):
        self.reservation = Reservation(
            start_at=self.field(Fields.START_AT).toPyDateTime(),
            end_at=self.field(Fields.END_AT).toPyDateTime(),
            comment=self.field(Fields.COMMENT),
            event_id=self._event.id,
            location_id=self.field(Fields.PLACE_ID),
        )
        
        if self.areasPage.location:
            self.reservation.areas = list(area for area in self.areasPage.location.areas if area.id in self.field(Fields.AREA_IDS))

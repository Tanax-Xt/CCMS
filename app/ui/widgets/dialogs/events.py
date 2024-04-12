from typing import Dict
from sqlmodel import Session, select

from PyQt6 import QtWidgets, QtCore

from app.db import ENGINE
from app.db.models import (
    EventType,
    Event,
    Location,
    Reservation,
    Scope,
)
from app.ui.widgets.alerts import validationError
from app.ui.widgets.wizards.reservation import ReservationWizard
from app.ui.widgets.dialogs.ext import DialogView


class EventCreateDialog(DialogView):
    model = Event
    ui_path = "app/ui/assets/dialogs/event-update.ui"

    @property
    def scope_radios(self) -> Dict[Scope, QtWidgets.QRadioButton]:
        return {
            Scope.ENTERTAINMENT: self.entertainmentRadioButton,
            Scope.ENLIGHTENMENT: self.enlightenmentRadioButton,
            Scope.EDUCATION: self.educationRadioButton,
        }

    def setup_ui(self) -> None:
        self.reservationButton.clicked.connect(self.showReservationWizard)

        with Session(ENGINE) as session:
            eventTypeNames = session.exec(select(EventType.name)).all()

        self.typeComboBox.addItems(eventTypeNames)
        self.dateDateTimeEdit.setMinimumDateTime(QtCore.QDateTime.currentDateTime())

    def create(self, commit=True) -> Event:
        with Session(ENGINE) as session:
            event = self.obj

            event.title = self.titleLineEdit.text()
            event.start_at = self.dateDateTimeEdit.dateTime().toPyDateTime()
            event.description = self.descriptionTextEdit.toPlainText()
            event.type_id = session.exec(select(EventType.id).where(EventType.name == self.typeComboBox.currentText())).first()
            event.scope = next(scope for scope, radio in self.scope_radios.items() if radio.isChecked())
            
            session.add(event)
            if commit:
                if hasattr(self, "reservation"):
                    session.add(self.reservation)
                session.commit()
            else:
                session.flush()
        return event
                
    def showReservationWizard(self):
        event = self.create(False)

        wizard = ReservationWizard(event, self)

        if not wizard.exec():
            return

        with Session(ENGINE) as session:
            location = session.get(Location, wizard.reservation.location_id)
            self.reservation = wizard.reservation
            self.locationLabel.setText(location.name)
            self.areasLabel.setEnabled(any(wizard.reservation.areas))
            self.areasListWidget.clear()
            self.areasListWidget.addItems(area.name for area in wizard.reservation.areas)

    def accept(self) -> None:
        if not self.titleLineEdit.text():
            validationError(self, "Название мероприятия должно быть заполнено!")
            return

        self.create()
        return super().accept()


class EventUpdateDialog(EventCreateDialog):
    title = "Редактирование мероприятия"

    def setup_ui(self) -> None:
        super().setup_ui()

        with Session(ENGINE) as session:
            session.add(self.obj)
            
            if any(self.obj.reservations):
                self.groupBox.setEnabled(False)
                reservation = session.exec(select(Reservation).where(Reservation.event_id == self.obj.id)).first()
                self.locationLabel.setText(reservation.location.name)
                self.areasListWidget.addItems(area.name for area in reservation.areas)

        self.titleLineEdit.setText(self.obj.title)
        self.descriptionTextEdit.setPlainText(self.obj.description)
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime(self.obj.start_at))
        self.scope_radios[self.obj.scope].setChecked(True)

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))

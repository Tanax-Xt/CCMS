from typing import Dict
from sqlmodel import Session, select

from PyQt6 import QtWidgets, QtCore

from app.db import ENGINE
from app.db.models import (
    Event,
    AssignmentType,
    Location,
    Assignment,
)
from app.ui.widgets.dialogs.ext import DialogView
        
        

class AssignmentCreateDialog(DialogView):
    model = Assignment
    ui_path = "app/ui/assets/dialogs/assignment-update.ui"

    @property
    def state_radios(self) -> Dict[Assignment.State, QtWidgets.QRadioButton]:
        return {
            Assignment.State.DRAFT: self.draftRadioButton,
            Assignment.State.ACTIVE: self.activeRadioButton,
            Assignment.State.COMPLETED: self.completedRadioButton,
        }

    def setup_ui(self):
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())

        with Session(ENGINE) as session:
            workTypeNames = session.exec(select(AssignmentType.name)).all()
            roomTypeNames = session.exec(select(Location.name)).all()
            eventNames = session.exec(select(Event.title)).all()

        self.typeComboBox.addItems(eventTypeName for eventTypeName in workTypeNames)
        self.roomComboBox.addItems(eventTypeName for eventTypeName in roomTypeNames)
        self.eventComboBox.addItems(eventTypeName for eventTypeName in eventNames)

    def accept(self) -> None:
        with Session(ENGINE) as session:
            assignment: Assignment = self.obj
            assignment.state = next(scope for scope, radio in self.state_radios.items() if radio.isChecked())
            assignment.deadline = self.dateDateTimeEdit.dateTime().toPyDateTime()
            assignment.description = self.descriptionTextEdit.toPlainText()
            assignment.event_id = session.exec(select(Event.id).where(Event.title == self.eventComboBox.currentText())).first()
            assignment.location_id = session.exec(select(Location.id).where(Location.name == self.roomComboBox.currentText())).first()
            assignment.type_id = session.exec(select(AssignmentType.id).where(AssignmentType.name == self.typeComboBox.currentText())).first()

            session.add(assignment)
            session.commit()

        return super().accept()


class AssignmentUpdateDialog(AssignmentCreateDialog):
    title = "Редактирование заявки"

    def setup_ui(self) -> None:
        super().setup_ui()

        self.state_radios[self.obj.state].setChecked(True)
        self.descriptionTextEdit.setPlainText(self.obj.description)
        self.dateDateTimeEdit.setDateTime(QtCore.QDateTime(self.obj.deadline))

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))
        if self.obj.event:
            self.eventComboBox.setCurrentIndex(self.eventComboBox.findText(self.obj.event.title))
        if self.obj.location:
            self.roomComboBox.setCurrentIndex(self.roomComboBox.findText(self.obj.location.name))
            
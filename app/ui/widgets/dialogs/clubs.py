from sqlmodel import Session, select

from PyQt6 import QtCore

from app.db import ENGINE
from app.db.models import (
    Club,
    ClubType,
    Location,
    Teacher,
)
from app.ui.widgets.dialogs.ext import DialogView
from app.ui.widgets.alerts import validationError
from app.ui.widgets.schedule import DaysScheduleManagerDialog


class ClubCreateDialog(DialogView):
    model = Club
    ui_path = "app/ui/assets/dialogs/club-update.ui"

    def setup_ui(self) -> None:
        self.schedule_manager = DaysScheduleManagerDialog(self.obj.days, self)
        self.schedule_manager.accepted.connect(self._update_schedule_type_label)
        self.editScheduleButton.clicked.connect(self.schedule_manager.exec)

        self.startDateEdit.setMinimumDate(QtCore.QDate.currentDate())

        with Session(ENGINE) as session:
            self.typeComboBox.addItems(session.exec(select(ClubType.name)).all())
            self.locationComboBox.addItems(session.exec(select(Location.name)).all())
            self.teacherComboBox.addItems(session.exec(select(Teacher.name)).all())

    def accept(self) -> None:
        if not self.titleLineEdit.text():
            validationError(self, "Название не должно быть пустым!")
            return
        if not self.obj.days and not self.schedule_manager.days:
            validationError(self, "Выберите хотя бы один день недели!")
            return

        with Session(ENGINE) as session:
            club: Club = self.obj
            club.days = self.schedule_manager.days
            club.title = self.titleLineEdit.text()
            club.start_at = self.startDateEdit.date().toPyDate()
            club.teacher_id = session.exec(select(Teacher.id).where(Teacher.name == self.teacherComboBox.currentText())).first()
            club.location_id = session.exec(select(Location.id).where(Location.name == self.locationComboBox.currentText())).first()
            club.type_id = session.exec(select(ClubType.id).where(ClubType.name == self.typeComboBox.currentText())).first()

            session.add(club)
            session.commit()

        return super().accept()

    def _update_schedule_type_label(self):
        self.scheduleTypeLabel.setText(str(len(self.schedule_manager.days)))


class ClubUpdateDialog(ClubCreateDialog):
    title = "Редактирование секции"
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.scheduleTypeLabel.setText(str(len(self.obj.days)))
    
        self.titleLineEdit.setText(self.obj.title)
        self.startDateEdit.setDate(QtCore.QDate(self.obj.start_at))

        if self.obj.type:
            self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(self.obj.type.name))
        if self.obj.teacher:
            self.teacherComboBox.setCurrentIndex(self.teacherComboBox.findText(self.obj.teacher.name))
        if self.obj.location:
            self.locationComboBox.setCurrentIndex(self.locationComboBox.findText(self.obj.location.name))
    

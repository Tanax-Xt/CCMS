from datetime import time

from PyQt6 import QtWidgets, QtCore

from app.db.models import Weekday, DaySchedule
from app.ui.widgets.mixins import WidgetMixin

WEEKDAY_NAMES = {
    Weekday.MONDAY: "Понедельник",
    Weekday.TUESDAY: "Вторник",
    Weekday.WEDNESDAY: "Среда",
    Weekday.THURSDAY: "Четверг",
    Weekday.FRIDAY: "Пятница",
    Weekday.SATURDAY: "Суббота",
    Weekday.SUNDAY: "Воскресенье",
}

DEFAULT_START_AT_TIME = time(14)
DEFAULT_END_AT_TIME = time(16)


class DayScheduleGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        weekday: Weekday,
        is_checked: bool = False,
        default_start_at_time: time = DEFAULT_START_AT_TIME,
        default_end_at_time: time = DEFAULT_END_AT_TIME,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(WEEKDAY_NAMES[weekday], parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setCheckable(True)
        self.setChecked(is_checked)

        self.weekday = weekday

        self.start_at_label = QtWidgets.QLabel("От", self)
        self.start_at_time_edit = QtWidgets.QTimeEdit(
            QtCore.QTime(default_start_at_time), self
        )

        self.end_at_label = QtWidgets.QLabel("до", self)
        self.end_at_time_edit = QtWidgets.QTimeEdit(
            QtCore.QTime(default_end_at_time), self
        )

        self.layout().addWidget(self.start_at_label)
        self.layout().addWidget(self.start_at_time_edit)
        self.layout().addWidget(self.end_at_label)
        self.layout().addWidget(self.end_at_time_edit)


MAX_COLUMN_COUNT = 2


class DaysScheduleManagerDialog(QtWidgets.QDialog, WidgetMixin):
    ui_path = "app/ui/assets/dialogs/schedule-manager.ui"

    def __init__(
        self, days: list[DaySchedule] = [], parent: QtWidgets.QWidget | None = None
    ) -> None:
        self.days: list[DaySchedule] = days
        super().__init__(parent)

    @property
    def weekdays(self):
        return frozenset(schedule_day.weekday for schedule_day in self.days)

    @property
    def boxes(self) -> set[DayScheduleGroupBox]:
        return frozenset(
            self.gridLayout.itemAt(i).widget() for i in range(self.gridLayout.count())
        )

    def setup_ui(self) -> None:
        weekday_days = {
            sd.weekday: DayScheduleGroupBox(sd.weekday, True, sd.start_at, sd.end_at)
            for sd in self.days
        }

        for i, weekday in enumerate(Weekday):
            box = weekday_days.get(weekday, DayScheduleGroupBox(weekday))

            col = i % MAX_COLUMN_COUNT
            row = i // MAX_COLUMN_COUNT + i - col
            self.gridLayout.addWidget(box, row, col)

    def accept(self) -> None:
        for box in self.boxes:
            day_schedule = next(
                (day for day in self.days if day.weekday == box.weekday), DaySchedule()
            )
            if box.isChecked():
                day_schedule.start_at = box.start_at_time_edit.time().toPyTime()
                day_schedule.end_at = box.end_at_time_edit.time().toPyTime()

                if day_schedule.weekday:
                    continue

                day_schedule.weekday = box.weekday
                self.days.append(day_schedule)
            elif day_schedule.id:
                self.days.remove(day_schedule)
            elif day_schedule.weekday:
                self.days = [day for day in self.days if day != day_schedule]

        return super().accept()

    def reject(self) -> None:
        for box in self.boxes:
            box.setChecked(box.weekday in self.weekdays)
        return super().reject()

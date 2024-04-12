from sqlmodel import Session

from app.ui.models import *
from app.ui.models.models import SCOPES, STATES
from app.ui.widgets.dialogs import *

from app.db import ENGINE
from app.db.models import *
from app.ui.widgets.tables.base import *
from app.ui.widgets.tables.filters import *
from app.ui.widgets.tables.filters import TextFilter, EnumFilter


class EventTable(Table):
    table = Event
    table_model = EventTableModel
    create_dialog = EventCreateDialog
    update_dialog = EventUpdateDialog
    filters = (
        TextFilter("Заголовок:", Event.title),
        TextFilter("Описание:", Event.description),
        ComboboxFilter("Вид:", EventType.name, True),
        EnumFilter("Пространтсво:", Event.scope, SCOPES),
        DateTimeRangeFilter("Начало:", Event.start_at, True),
        DateTimeRangeFilter("Дата создания:", Event.created_at, True),
    )


class AssignmentTable(Table):
    table = Assignment
    table_model = AssignmentTableModel
    create_dialog = AssignmentCreateDialog
    update_dialog = AssignmentUpdateDialog
    filters = (
        ComboboxFilter("Вид:", AssignmentType.name, True),
        ComboboxFilter("Локация:", Location.name),
        EnumFilter("Статус:", Assignment.state, STATES),
        DateTimeRangeFilter("Дедлайн:", Assignment.deadline, True),
        DateTimeRangeFilter("Дата создания:", Assignment.created_at, True),
    )


class DesktopTable(AssignmentTable):
    create_dialog = None
    update_dialog = None
    delete_visible = False
    filters = (
        ComboboxFilter("Вид:", AssignmentType.name),
        ComboboxFilter("Локация:", Location.name),
        DateTimeRangeFilter("Дедлайн:", Assignment.deadline, True),
        DateTimeRangeFilter("Дата создания:", Assignment.created_at, True),
    )
    
    @property
    def statement(self):
        return super().statement.where(Assignment.state == Assignment.State.ACTIVE)

    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_extra_button("Пометить как выполненное", self.mark_as_completed, "app/ui/resourses/check.png")
        
    def mark_as_completed(self) -> None:
        with Session(ENGINE) as session:
            assignments = []
            for i, j in enumerate(self.selected_indexes):
                index = j - i
                assignment: Assignment = self.model._data[index]
                assignment.state = Assignment.State.COMPLETED
                assignments.append(assignment)
                self.model.removeRow(index)
            session.bulk_save_objects(assignments)
            session.commit()

        self.update_total_count()
  
  
class ReservationTable(Table):
    table = Reservation
    table_model = ReservaionTableModel
    filters = (
        TextFilter("Комментарий:", Reservation.comment),
        ComboboxFilter("Локация:", Location.name, True),
        DateTimeRangeFilter("Начало:", Reservation.start_at, True),
        DateTimeRangeFilter("Конец:", Reservation.end_at, True),
        DateTimeRangeFilter("Дата создания:", Reservation.created_at, True),
    )
    
    def setup_ui(self) -> None:
        super().setup_ui()
        self.add_top_button("Зоны", self.showAreasManager, "app/ui/resourses/categorize.png")

    def showAreasManager(self):
        AreaManagerDialog(self).exec()
        self.refresh()
        
        
class EducationTable(Table):
    table = Club
    table_model = ClubTableModel
    create_dialog = ClubCreateDialog
    update_dialog = ClubUpdateDialog
    filters = (
        ComboboxFilter("Вид:", ClubType.name, True),
        ComboboxFilter("Преподаватель:", Teacher.name, True),
        DateTimeRangeFilter("Старт:", Club.start_at, True),
        DateTimeRangeFilter("Дата создания:", Club.created_at, True),
    )

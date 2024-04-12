from enum import Enum, auto
from typing import Optional, List, Set
from datetime import date, time, datetime

from sqlmodel import SQLModel, Field, Relationship

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declared_attr


class Scope(Enum):
    """Represents a scope to categorize events.

    Attributes:
        ENTERTAINMENT: The entertainment scope.
        ENLIGHTENMENT: The enlightenment scope.
        EDUCATION: The ignored scope at the moment.
    """

    ENTERTAINMENT = auto()
    ENLIGHTENMENT = auto()
    EDUCATION = auto()


class Weekday(Enum):
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()

    @classmethod
    def from_date(cls, date: date):
        return cls(date.isoweekday())


class BaseModel(SQLModel):
    """A base model for database entities.

    Attributes:
        id (Optional[int]): The unique identifier for this object.
        created_at (datetime): The identity date and time for this object.
    """

    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        return cls.__name__


class UniqueNamedModel(BaseModel):
    """A base model for unique named entities.

    Attributes:
        name (str): The unique name of this object.
    """

    name: str = Field(max_length=128, unique=True, index=True)


class AreaReservationLink(SQLModel, table=True):
    """A class representing the many-to-many relationship with area and reservation.

    Attributes:
        area_id (Optional[int]): The unique identifier of the associated area.
        reservation_id (Optional[int]): The unique identifier of the associated reservation.
    """

    area_id: Optional[int] = Field(
        default=None, foreign_key="Area.id", primary_key=True
    )
    reservation_id: Optional[int] = Field(
        default=None, foreign_key="Reservation.id", primary_key=True
    )


class Location(UniqueNamedModel, table=True):
    """A class representing a location.

    Attributes:
        areas (List[Area]): The list of areas associated with this location.
        events (List[Event]): The list of events associated with this location.
        assignments (List[Assignment]): The list of assignments associated with this location.
        reservations (List[Reservation]): The list of reservations associated with this location.
        clubs (List[Club]): The list of clubs associated with this location.
    """

    areas: List["Area"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    events: List["Event"] = Relationship(back_populates="location")
    assignments: List["Assignment"] = Relationship(back_populates="location")
    reservations: List["Reservation"] = Relationship(
        back_populates="location",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    clubs: List["Club"] = Relationship(back_populates="location")

    def __str__(self) -> str:
        return self.name


class Area(BaseModel, table=True):
    """A class representing a part of a location.

    Attributes:
        name (str): The unique name of this area.
        location_id (Optional[int]): The unique identifier of the associated location.
        location (Optional[Location]): The location associated with this area.
        reservations (List[Reservation]): The list of reservations associated with this area.
    """

    name: str = Field(max_length=128, index=True)

    location_id: Optional[int] = Field(default=None, foreign_key="Location.id")
    location: Optional[Location] = Relationship(back_populates="areas")

    reservations: List["Reservation"] = Relationship(
        back_populates="areas", link_model=AreaReservationLink
    )

    __table_args__ = (UniqueConstraint("name", "location_id"),)


class EventType(UniqueNamedModel, table=True):
    """A class representing an event type.

    Attributes:
        events (List[Event]): The list of events associated with this event type.
    """

    events: List["Event"] = Relationship(back_populates="type")


class Event(BaseModel, table=True):
    """Represents an event registered on a specific date.

    Attributes:
        title (str): The title of this event.
        description (Optional[str]): The description of this event.
        start_at (datetime): The start date and time of this event.
        scope (Scope): The scope of this event.
        type_id (Optional[int]): The unique identifier of the associated event type.
        type (Optional[EventType]): The event type associated with this event.
        location_id (Optional[int]): The unique identifier of the associated location.
        location (Optional[Location]): The associated location of the event.
        assignments (List[Assignment]): The list of assignments associated with this event.
        reservations (List[Reservation]): The list of reservations associated with this event.
    """

    title: str = Field(max_length=256, index=True)
    description: Optional[str] = Field(default=None, max_length=1028)
    start_at: datetime
    scope: Scope

    type_id: Optional[int] = Field(default=None, foreign_key="EventType.id")
    type: Optional[EventType] = Relationship(back_populates="events")

    location_id: Optional[int] = Field(default=None, foreign_key="Location.id")
    location: Optional[Location] = Relationship(back_populates="events")

    assignments: List["Assignment"] = Relationship(back_populates="event")
    reservations: List["Reservation"] = Relationship(
        back_populates="event",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


class AssignmentType(UniqueNamedModel, table=True):
    """A class representing an assignment type.

    Attributes:
        assignments (List[Assignment]): The list of assignments associated with this assignment type.
    """

    assignments: List["Assignment"] = Relationship(back_populates="type")


class Assignment(BaseModel, table=True):
    """A class representing an assignment to an event.

    Attributes:
        state (State): The state of this assignment.
        deadline (datetime): The deadline of this assignment.
        description (Optional[str]): The description of this assignment.
        event_id (Optional[int]): The unique identifier of the associated event.
        event (Event): The event associated with this assignment.
        type_id (Optional[int]): The unique identifier of the assignment type.
        type (AssignmentType): The assignment type object.
        location_id (Optional[int]): The unique identifier of the associated location.
        location (Location): The location associated with this assignment.
    """

    class State(Enum):
        """Enumeration representing the state of an assignment.

        Attributes:
            DRAFT: The assignment is in the draft state.
            ACTIVE: The assignment is active at the moment.
            COMPLETED: The assignment has been marked as completed.
        """

        DRAFT = auto()
        ACTIVE = auto()
        COMPLETED = auto()

    state: State = State.DRAFT
    deadline: datetime
    description: Optional[str] = Field(default=None, max_length=1028)

    type_id: Optional[int] = Field(default=None, foreign_key="AssignmentType.id")
    type: Optional[AssignmentType] = Relationship(back_populates="assignments")

    location_id: Optional[int] = Field(default=None, foreign_key="Location.id")
    location: Optional[Location] = Relationship(back_populates="assignments")

    event_id: Optional[int] = Field(default=None, foreign_key="Event.id")
    event: Optional[Event] = Relationship(back_populates="assignments")


class Reservation(BaseModel, table=True):
    """A class representing a location reservation for an event.

    Attributes:
        start_at (datetime): The start time of the reservation.
        end_at (datetime): The end time of the reservation.
        comment (Optional[str]): An optional comment for the reservation.
        event_id (Optional[int]): The unique identifier of the associated event.
        event (Event): The event associated with this reservation.
        location_id (Optional[int]): The unique identifier of the associated location.
        location (Location): The location associated with this reservation.
        areas (List[Area]): The list of areas associated with this reservation.
    """

    start_at: datetime
    end_at: datetime
    comment: Optional[str] = Field(default=None, max_length=1028)

    event_id: Optional[int] = Field(default=None, foreign_key="Event.id")
    event: Event = Relationship(back_populates="reservations")

    location_id: Optional[int] = Field(default=None, foreign_key="Location.id")
    location: Location = Relationship(back_populates="reservations")

    areas: List[Area] = Relationship(
        back_populates="reservations", link_model=AreaReservationLink
    )


class Teacher(UniqueNamedModel, table=True):
    """A class representing a teacher.

    Attributes:
        clubs (List[Club]): The list of clubs associated with this teacher.
    """

    clubs: List["Club"] = Relationship(back_populates="teacher")


class ClubType(UniqueNamedModel, table=True):
    """A class representing a club type.

    Attributes:
        clubs (List[Club]): The list of clubs associated with this club type.
    """

    clubs: List["Club"] = Relationship(back_populates="type")


class DaySchedule(BaseModel, table=True):
    """A class representing a day schedule.

    Attributes:
        weekday (Weekday): The weekday of this club day.
        start_at (time): The start time of this club day.
        end_at (time): The end time of this club day.
        club_id (Optional[int]): The unique identifier of the associated club.
        club (Optional[Club]): The club associated with this assignment.
    """

    weekday: Weekday
    start_at: time
    end_at: time

    club_id: Optional[int] = Field(default=None, foreign_key="Club.id")
    club: Optional["Club"] = Relationship(back_populates="days")


class Club(BaseModel, table=True):
    """Represents a club registered on a specific date.

    Attributes:
        title (str): The title of this club.
        start_at (date): The start date of this club.
        type_id (Optional[int]): The unique identifier of the associated club type.
        type (Optional[EventType]): The club type associated with this club.
        location_id (Optional[int]): The unique identifier of the associated location.
        location (Optional[Location]): The associated location of this club.
        days (List[ClubDay]): The list of days in the schedule of this club.
    """

    title: str = Field(max_length=256, index=True)
    start_at: date

    type_id: Optional[int] = Field(default=None, foreign_key="ClubType.id")
    type: Optional[ClubType] = Relationship(back_populates="clubs")

    teacher_id: Optional[int] = Field(default=None, foreign_key="Teacher.id")
    teacher: Optional[Teacher] = Relationship(back_populates="clubs")

    location_id: Optional[int] = Field(default=None, foreign_key="Location.id")
    location: Optional[Location] = Relationship(back_populates="clubs")

    days: List[DaySchedule] = Relationship(
        back_populates="club",
        sa_relationship_kwargs={"cascade": "all, delete, delete-orphan"},
    )

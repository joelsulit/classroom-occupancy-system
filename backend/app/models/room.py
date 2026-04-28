from datetime import datetime, date, time
from app.extensions import db

class Campus(db.Model):
    __tablename__ = "campuses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # MAIN | ANNEX | CPAG
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buildings = db.relationship("Building", backref="campus", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_buildings: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
        }
        if include_buildings:
            data["buildings"] = [b.to_dict() for b in self.buildings]
        return data

    def __repr__(self):
        return f"<Campus {self.code}>"


class Building(db.Model):
    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(30), nullable=False)       # e.g. CEIT, CABA
    campus_id = db.Column(db.Integer, db.ForeignKey("campuses.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("code", "campus_id", name="uq_building_code_campus"),
    )

    rooms = db.relationship("Room", backref="building", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_rooms: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "campus_id": self.campus_id,
            "campus": self.campus.name if self.campus else None,
            "description": self.description,
        }
        if include_rooms:
            data["rooms"] = [r.to_dict() for r in self.rooms]
        return data

    def __repr__(self):
        return f"<Building {self.code}>"

ROOM_TYPES = ("lecture", "laboratory", "conference", "office", "other")


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)       # e.g. "Room 301"
    code = db.Column(db.String(50), nullable=False)        # e.g. "CEIT-301"
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False, index=True)
    floor = db.Column(db.Integer, nullable=True)
    room_type = db.Column(db.String(20), nullable=False, default="lecture")
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("code", "building_id", name="uq_room_code_building"),
    )

    reservations = db.relationship("Reservation", backref="room", lazy="dynamic", cascade="all, delete-orphan")


    def is_occupied_at(self, check_date: date, check_time: time) -> bool:
        """Return True if an approved reservation covers the given date/time."""
        from app.models.reservation import Reservation, ReservationStatus
        return (
            self.reservations.filter(
                Reservation.status == ReservationStatus.APPROVED,
                Reservation.date == check_date,
                Reservation.start_time <= check_time,
                Reservation.end_time > check_time,
            ).count()
            > 0
        )

    def current_reservation(self):
        """Return the active approved reservation right now, if any."""
        from app.models.reservation import Reservation, ReservationStatus
        now = datetime.utcnow()  # store UTC; convert as needed
        today = now.date()
        current_time = now.time().replace(second=0, microsecond=0)
        return (
            self.reservations.filter(
                Reservation.status == ReservationStatus.APPROVED,
                Reservation.date == today,
                Reservation.start_time <= current_time,
                Reservation.end_time > current_time,
            ).first()
        )

    def to_dict(self, include_occupancy: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "building_id": self.building_id,
            "building": self.building.name if self.building else None,
            "campus": self.building.campus.name if self.building and self.building.campus else None,
            "campus_code": self.building.campus.code if self.building and self.building.campus else None,
            "floor": self.floor,
            "room_type": self.room_type,
            "is_active": self.is_active,
            "notes": self.notes,
        }
        if include_occupancy:
            current = self.current_reservation()
            data["is_occupied"] = current is not None
            data["current_reservation"] = current.to_dict(include_room=False) if current else None
        return data

    def __repr__(self):
        return f"<Room {self.code}>"
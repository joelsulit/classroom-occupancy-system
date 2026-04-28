from datetime import datetime
from app.extensions import db
import enum

class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False, index=True)

    requestor_name = db.Column(db.String(150), nullable=False)       
    course_section = db.Column(db.String(100), nullable=False)       
    purpose = db.Column(db.Text, nullable=True)                      
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default=ReservationStatus.PENDING,
        index=True,
    )
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    review_note = db.Column(db.Text, nullable=True)    
    reviewed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    reviewer = db.relationship("User", foreign_keys=[reviewed_by], backref="reviewed_reservations")

    @staticmethod
    def has_conflict(room_id: int, date, start_time, end_time, exclude_id: int = None) -> bool:

        query = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.date == date,
            Reservation.status.in_([ReservationStatus.APPROVED, ReservationStatus.PENDING]),
            Reservation.start_time < end_time,
            Reservation.end_time > start_time,
        )
        if exclude_id:
            query = query.filter(Reservation.id != exclude_id)
        return query.count() > 0

    def to_dict(self, include_room: bool = True) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "requestor_name": self.requestor_name,
            "course_section": self.course_section,
            "purpose": self.purpose,
            "date": self.date.isoformat() if self.date else None,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
            "status": self.status,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_room and self.room:
            data["room"] = self.room.to_dict()
        else:
            data["room_id"] = self.room_id
        return data

    def __repr__(self):
        return f"<Reservation #{self.id} room={self.room_id} {self.date} {self.start_time}-{self.end_time} [{self.status}]>"


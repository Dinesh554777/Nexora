from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.analysis import Analysis


class Patient(Base):
    """A patient record associated with one or more analyses."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    contact_info: Mapped[str | None] = mapped_column(String(256), nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=func.true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    @property
    def patient_code(self) -> str:
        return self.patient_id

    @patient_code.setter
    def patient_code(self, value: str) -> None:
        self.patient_id = value

    @property
    def gender(self) -> str:
        return self.sex

    @gender.setter
    def gender(self, value: str) -> None:
        self.sex = value

    def __repr__(self) -> str:
        return f"<Patient id={self.id} patient_id={self.patient_id!r} name={self.name!r}>"

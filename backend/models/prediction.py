from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from database.base import Base


class Prediction(Base):
    """One segmentation pipeline execution and its outcome metadata.

    Only lightweight metadata is stored. Mask/overlay pixels are returned
    inline by the API and are intentionally NOT persisted as blobs; if file
    storage is added later, reference columns belong here.
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    analysis_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("analyses.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    image_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    execution_time_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped["Analysis | None"] = relationship(back_populates="predictions")
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

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} status={self.status!r} "
            f"filename={self.original_filename!r}>"
        )

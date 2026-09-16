"""Model da tabela photos."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Photo(Base):
    """Uma obra do catalogo, em print ou quadro."""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # retrato | paisagem | urbano | autoral
    category: Mapped[str | None] = mapped_column(Text)
    # print | quadro
    medium: Mapped[str] = mapped_column(Text, nullable=False)
    sizes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

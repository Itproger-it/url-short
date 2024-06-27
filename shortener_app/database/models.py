# shortener_app/models.py

from sqlalchemy.orm import Mapped, mapped_column

from . import Model

class URL(Model):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(unique=True, index=True)
    secret_key: Mapped[str] = mapped_column(unique=True, index=True)
    target_url: Mapped[str] = mapped_column(index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    clicks: Mapped[int] = mapped_column(default=0)
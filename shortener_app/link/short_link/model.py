from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, BigInteger

from shortener_app.database import Model


class URL(Model):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(unique=True, index=True)
    secret_key: Mapped[str] = mapped_column(unique=True, index=True)
    target_url: Mapped[str] = mapped_column(index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    clicks: Mapped[int] = mapped_column(default=0)


class AuthUserUrl(Model):
    __tablename__ = "auth_user_url"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("api_user.id", ondelete="CASCADE"), nullable=False)
    url_id: Mapped[int] = mapped_column(ForeignKey("url.id", ondelete="CASCADE"), nullable=False)


class UrlMetric(Model):
    __tablename__ = "url_metric"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("url.id", ondelete="CASCADE"), nullable=False)
    ip: Mapped[str]
    device: Mapped[str]
    date: Mapped[str]

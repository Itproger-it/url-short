from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Model


class APIUser(Model):
    __tablename__ = "api_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]

    tokens = relationship('IssuedJWTToken', back_populates='subject')


    def __str__(self) -> str:
        return self.email
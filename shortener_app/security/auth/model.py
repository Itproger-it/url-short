from shortener_app.database import Model, str_36
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey


class IssuedJWTToken(Model):
    __tablename__ = "issued_jwt_token"
    jti: Mapped[str_36] = mapped_column(primary_key=True)

    subject_id: Mapped[int] = mapped_column(ForeignKey('api_user.id', ondelete='CASCADE'), nullable=False)
    device_id: Mapped[str_36]
    revoked: Mapped[bool] = mapped_column(default=False)

    subject = relationship("APIUser", back_populates="tokens")


    def __str__(self) -> str:
        return f'{self.subject}: {self.jti}'
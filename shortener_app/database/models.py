# shortener_app/models.py

from sqlalchemy.orm import Mapped, mapped_column

from . import Model
from ..user.model import APIUser
from ..security.auth.model import IssuedJWTToken
from ..link.short_link.model import URL, AuthUserUrl, UrlMetric
from .dto import UserProfileDTO
from .model import APIUser


class MeService:
    def get_me(self, user: APIUser) -> UserProfileDTO:
        return UserProfileDTO(email=user.email)
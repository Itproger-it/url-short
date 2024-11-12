from pydantic import BaseModel


class UserProfileDTO(BaseModel):
    email: str

    class Config:
        orm_mode = True
from pydantic import BaseModel

class URLBase(BaseModel):
    target_url: str

class URLDecodeBase(BaseModel):
    url: str
  
class URLDecode(BaseModel):
    url: str 

class URL(URLBase):
    is_active: bool
    clicks: int

    class Config:
        orm_mode = True

class URLInfo(URL):
    url: str
    admin_url: str

class URLCustom(URLBase):
    name: str


class UserLinks(URLBase):
    clicks: int
    key: str
    secret_key: str

    class Config:
        orm_mode = True

class UrlMetric(BaseModel):
    device: str
    ip: str
    date: str

    class Config:
        orm_mode = True
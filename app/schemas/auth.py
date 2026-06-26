from pydantic import BaseModel


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    recaptcha_token: str


class UserLogin(BaseModel):
    email: str
    password: str
    recaptcha_token: str


class AdminCreate(BaseModel):
    full_name: str
    username: str
    password: str
    email: str
    admin_level: int


class AdminLogin(BaseModel):
    username_or_email: str
    password: str

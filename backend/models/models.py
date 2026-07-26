from pydantic import EmailStr, BaseModel


class WaitlistSignup(BaseModel):
    email: EmailStr
    name: str | None = None

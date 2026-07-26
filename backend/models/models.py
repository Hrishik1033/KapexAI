from pydantic import EmailStr, BaseModel


class WaitlistSignup(BaseModel):
    email: EmailStr
    name: str | None = None

class CreateChatSession(BaseModel):
    email: EmailStr
    business_idea: str
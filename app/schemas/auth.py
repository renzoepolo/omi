from pydantic import BaseModel, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str

    @model_validator(mode="after")
    def normalize_identity(self) -> "LoginRequest":
        # Backward compatibility: some clients still send "username".
        email = (self.email or "").strip()
        username = (self.username or "").strip()
        self.email = email or username
        if not self.email:
            raise ValueError("Either email or username is required")
        return self

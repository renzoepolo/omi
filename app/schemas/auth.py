from pydantic import BaseModel, EmailStr, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    username: EmailStr | None = None
    password: str

    @model_validator(mode="after")
    def normalize_identity(self) -> "LoginRequest":
        # Backward compatibility: some clients still send "username".
        self.email = self.email or self.username
        if not self.email:
            raise ValueError("Either email or username is required")
        return self

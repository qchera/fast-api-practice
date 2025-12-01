from pydantic import ConfigDict, BaseModel, Field
from pydantic.alias_generators import to_camel
from sqlmodel import SQLModel

class CamelModel(SQLModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class PasswordResetModel(CamelModel):
    token: str
    new_password: str
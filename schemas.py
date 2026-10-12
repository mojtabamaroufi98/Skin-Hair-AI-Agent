from typing import Optional

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="User's question"
    )

    age: Optional[int] = Field(
        default=None,
        ge=1,
        le=120,
        description="User age"
    )

    skin_type: Optional[str] = Field(
        default=None,
        description="Skin type"
    )

    hair_type: Optional[str] = Field(
        default=None,
        description="Hair type"
    )

    user_id: Optional[str] = Field(
        default=None,
        description="Optional user identifier"
    )


class AgentResponse(BaseModel):
    success: bool
    answer: str
    session_id: Optional[str] = None
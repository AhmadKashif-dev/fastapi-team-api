from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class OrgCreate(BaseModel):
    name: str


class OrgRead(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrgUpdate(BaseModel):
    name: str | None = None


class MemberRead(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role_id: UUID
    status: str

    model_config = {"from_attributes": True}


class MemberReadWithUser(BaseModel):
    id: UUID
    user_id: UUID
    role_id: UUID
    role_name: str | None = None
    status: str
    email: str
    full_name: str | None
    joined_at: datetime | None = None

    model_config = {"from_attributes": True}


class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: UUID


class InvitationRead(BaseModel):
    id: UUID
    email: str
    organization_id: UUID
    role_id: UUID
    invited_by_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssign(BaseModel):
    role_id: UUID


class InvitationAccept(BaseModel):
    token: str
    password: str | None = None
    full_name: str | None = None

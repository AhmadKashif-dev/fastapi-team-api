from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, hash_token
from app.database import get_db
from app.models import Invitation, Membership, MembershipStatus, User
from app.schemas.organization import InvitationAccept

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/accept")
def accept_invitation(
    data: InvitationAccept,
    db: Session = Depends(get_db),
):
    token_hash = hash_token(data.token)
    inv = db.query(Invitation).filter(Invitation.token_hash == token_hash).first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token",
        )
    if inv.accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already accepted",
        )
    if inv.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    user = db.query(User).filter(User.email == inv.email).first()
    if not user:
        if not data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required for new user",
            )
        user = User(
            email=inv.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        db.flush()

    existing = (
        db.query(Membership)
        .filter(
            Membership.user_id == user.id,
            Membership.organization_id == inv.organization_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already a member of this organization",
        )

    membership = Membership(
        user_id=user.id,
        organization_id=inv.organization_id,
        role_id=inv.role_id,
        status=MembershipStatus.ACCEPTED,
        invited_by_id=inv.invited_by_id,
        joined_at=datetime.utcnow(),
    )
    db.add(membership)

    inv.accepted_at = datetime.utcnow()
    inv.accepted_by_id = user.id

    db.commit()
    return {"message": "Invitation accepted", "user_id": str(user.id)}

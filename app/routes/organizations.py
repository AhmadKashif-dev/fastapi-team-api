import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_membership, require_permission
from app.auth.hashing import hash_token
from app.database import get_db
from app.models import Invitation, Membership, MembershipStatus, Organization, Role, User
from app.schemas.common import PaginatedResponse
from app.schemas.organization import (
    InvitationCreate,
    InvitationRead,
    MemberReadWithUser,
    OrgCreate,
    OrgRead,
    OrgUpdate,
    RoleAssign,
)
from app.services.mail import send_invitation_email

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _get_admin_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == "admin").first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin role not found. Run seed_roles.",
        )
    return role


@router.post("", response_model=OrgRead)
def create_organization(
    data: OrgCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_role = _get_admin_role(db)
    org = Organization(name=data.name, owner_id=user.id)
    db.add(org)
    db.flush()
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role_id=admin_role.id,
        status=MembershipStatus.ACCEPTED,
        joined_at=datetime.utcnow(),
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return org


@router.get("", response_model=PaginatedResponse[OrgRead])
def list_organizations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by organization name"),
    sort_by: str = Query("name", description="Sort by: name, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
):
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    org_ids = [m.organization_id for m in memberships]
    q = db.query(Organization).filter(Organization.id.in_(org_ids))

    if search:
        q = q.filter(Organization.name.ilike(f"%{search}%"))

    sort_col = Organization.name if sort_by == "name" else Organization.created_at
    if sort_order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    total = q.count()
    orgs = q.offset((page - 1) * limit).limit(limit).all()
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedResponse(
        items=orgs,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{org_id}", response_model=OrgRead)
def get_organization(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_membership(db, user.id, org_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrgRead)
def update_organization(
    org_id: UUID,
    data: OrgUpdate,
    user: User = Depends(require_permission("organization:update")),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if data.name is not None:
        org.name = data.name
    db.commit()
    db.refresh(org)
    return org


@router.delete("/{org_id}")
def delete_organization(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if org.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete the organization",
        )
    db.delete(org)
    db.commit()
    return {"message": "Organization deleted"}


@router.get("/{org_id}/members", response_model=PaginatedResponse[MemberReadWithUser])
def list_members(
    org_id: UUID,
    user: User = Depends(require_permission("member:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by full name or email"),
    role_id: UUID | None = Query(None, description="Filter by role"),
    sort_by: str = Query("full_name", description="Sort by: full_name, email, joined_at, role"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
):
    q = (
        db.query(Membership)
        .join(User, Membership.user_id == User.id)
        .join(Role, Membership.role_id == Role.id)
        .filter(
            Membership.organization_id == org_id,
            Membership.status == MembershipStatus.ACCEPTED,
        )
    )

    if search:
        term = f"%{search}%"
        q = q.filter(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )

    if role_id:
        q = q.filter(Membership.role_id == role_id)

    sort_map = {
        "full_name": User.full_name,
        "email": User.email,
        "joined_at": Membership.joined_at,
        "role": Role.name,
    }
    sort_col = sort_map.get(sort_by, User.full_name)
    if sort_order == "desc":
        q = q.order_by(sort_col.desc().nullslast())
    else:
        q = q.order_by(sort_col.asc().nullsfirst())

    total = q.count()
    memberships = q.offset((page - 1) * limit).limit(limit).all()

    result = []
    for m in memberships:
        u = m.user
        result.append(
            MemberReadWithUser(
                id=m.id,
                user_id=m.user_id,
                role_id=m.role_id,
                role_name=m.role.name,
                status=m.status.value,
                email=u.email,
                full_name=u.full_name,
                joined_at=m.joined_at,
            )
        )

    pages = (total + limit - 1) // limit if total > 0 else 1
    return PaginatedResponse(
        items=result,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post("/{org_id}/invitations", response_model=InvitationRead)
def create_invitation(
    org_id: UUID,
    data: InvitationCreate,
    user: User = Depends(require_permission("member:invite")),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    existing = db.query(Invitation).filter(
        Invitation.organization_id == org_id,
        Invitation.email == data.email,
        Invitation.accepted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitation already sent to this email",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    inv = Invitation(
        email=data.email,
        organization_id=org_id,
        role_id=data.role_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
        invited_by_id=user.id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    send_invitation_email(inv.email, org.name, user.full_name, token)
    return inv


@router.get("/{org_id}/invitations", response_model=PaginatedResponse[InvitationRead])
def list_invitations(
    org_id: UUID,
    user: User = Depends(require_permission("member:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by email"),
    sort_by: str = Query("created_at", description="Sort by: email, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
):
    q = db.query(Invitation).filter(
        Invitation.organization_id == org_id,
        Invitation.accepted_at.is_(None),
    )

    if search:
        q = q.filter(Invitation.email.ilike(f"%{search}%"))

    sort_col = Invitation.email if sort_by == "email" else Invitation.created_at
    if sort_order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    total = q.count()
    invs = q.offset((page - 1) * limit).limit(limit).all()
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedResponse(
        items=invs,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.delete("/{org_id}/invitations/{inv_id}")
def revoke_invitation(
    org_id: UUID,
    inv_id: UUID,
    user: User = Depends(require_permission("member:invite")),
    db: Session = Depends(get_db),
):
    inv = (
        db.query(Invitation)
        .filter(Invitation.id == inv_id, Invitation.organization_id == org_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    db.delete(inv)
    db.commit()
    return {"message": "Invitation revoked"}


@router.patch("/{org_id}/members/{user_id}/role")
def assign_member_role(
    org_id: UUID,
    user_id: UUID,
    data: RoleAssign,
    user: User = Depends(require_permission("member:assign_role")),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == org_id,
            Membership.user_id == user_id,
            Membership.status == MembershipStatus.ACCEPTED,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    membership.role_id = data.role_id
    db.commit()
    return {"message": "Role updated"}


@router.delete("/{org_id}/members/{user_id}")
def remove_member(
    org_id: UUID,
    user_id: UUID,
    user: User = Depends(require_permission("member:remove")),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if org.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner",
        )
    membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == org_id,
            Membership.user_id == user_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(membership)
    db.commit()
    return {"message": "Member removed"}

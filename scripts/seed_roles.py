"""
Seed default roles and permissions. Run after: alembic upgrade head

    python -m scripts.seed_roles
"""
import uuid

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Role, Permission, RolePermission


def seed_roles_and_permissions(db: Session) -> None:
    # Permissions
    perms_data = [
        {"name": "organization:create", "resource": "organization", "action": "create"},
        {"name": "organization:read", "resource": "organization", "action": "read"},
        {"name": "organization:update", "resource": "organization", "action": "update"},
        {"name": "organization:delete", "resource": "organization", "action": "delete"},
        {"name": "member:invite", "resource": "member", "action": "invite"},
        {"name": "member:remove", "resource": "member", "action": "remove"},
        {"name": "member:assign_role", "resource": "member", "action": "assign_role"},
        {"name": "member:read", "resource": "member", "action": "read"},
    ]

    permissions = {}
    for p in perms_data:
        perm = db.query(Permission).filter(Permission.name == p["name"]).first()
        if not perm:
            perm = Permission(id=uuid.uuid4(), **p)
            db.add(perm)
        permissions[p["name"]] = perm

    # Roles: admin (all), member (read-only for org/members)
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            id=uuid.uuid4(),
            name="admin",
            description="Organization administrator",
            is_system=True,
        )
        db.add(admin_role)
        db.flush()
        for perm in permissions.values():
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

    member_role = db.query(Role).filter(Role.name == "member").first()
    if not member_role:
        member_role = Role(
            id=uuid.uuid4(),
            name="member",
            description="Organization member",
            is_system=True,
        )
        db.add(member_role)
        db.flush()
        for name in ["organization:read", "member:read"]:
            db.add(
                RolePermission(
                    role_id=member_role.id,
                    permission_id=permissions[name].id,
                )
            )

    db.commit()
    print("Seeded roles: admin, member")
    print("Seeded permissions and role_permissions")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
    finally:
        db.close()

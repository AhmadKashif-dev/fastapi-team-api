from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import models to register them with Base.metadata
from app.models import (  # noqa: E402, F401
    User,
    Organization,
    Membership,
    Role,
    Permission,
    RolePermission,
    RefreshToken,
    PasswordResetToken,
    Invitation,
)

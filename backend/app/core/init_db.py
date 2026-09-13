"""Database Initialization & Seeding Script for Roles, Permissions, and Default Users."""

from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.auth import User, Role, Permission
from app.core.security import hash_password


def init_db(db: Session) -> None:
    import app.models  # Register all SQLAlchemy models on Base.metadata
    # Create tables on the active session engine
    Base.metadata.create_all(bind=db.get_bind())



    # Check if roles already exist
    if db.query(Role).first():
        return

    # 1. Create Fine-Grained Permissions
    permissions_map = {
        "case:create": Permission(name="case:create", description="Create new forensic case contexts"),
        "case:read": Permission(name="case:read", description="View case details and access list"),
        "case:close": Permission(name="case:close", description="Close active forensic cases"),
        "evidence:create": Permission(name="evidence:create", description="Attach evidence items to cases"),
        "evidence:read": Permission(name="evidence:read", description="View evidence metadata"),
        "job:sanitization": Permission(name="job:sanitization", description="Execute drive sanitization dry-runs"),
        "job:recovery": Permission(name="job:recovery", description="Execute evidence recovery tasks"),
    }

    for p in permissions_map.values():
        db.add(p)
    db.commit()

    # 2. Create Roles with Associated Permissions
    role_admin = Role(
        name="Administrator",
        description="Full system administration & security privilege",
        permissions=list(permissions_map.values()),
    )

    role_investigator = Role(
        name="Investigator",
        description="Lead forensic case investigator",
        permissions=[
            permissions_map["case:create"],
            permissions_map["case:read"],
            permissions_map["case:close"],
            permissions_map["evidence:create"],
            permissions_map["evidence:read"],
            permissions_map["job:recovery"],
        ],
    )

    role_operator = Role(
        name="Operator",
        description="Forensic operation specialist",
        permissions=[
            permissions_map["case:read"],
            permissions_map["evidence:read"],
            permissions_map["job:sanitization"],
            permissions_map["job:recovery"],
        ],
    )

    role_viewer = Role(
        name="Viewer",
        description="Read-only audit spectator",
        permissions=[
            permissions_map["case:read"],
            permissions_map["evidence:read"],
        ],
    )

    db.add_all([role_admin, role_investigator, role_operator, role_viewer])
    db.commit()

    # 3. Create Default Seed Users for Testing & Initial Setup
    users = [
        User(
            username="admin",
            email="admin@forensicshield.local",
            hashed_password=hash_password("AdminPass123!"),
            role_id=role_admin.id,
        ),
        User(
            username="investigator1",
            email="investigator1@forensicshield.local",
            hashed_password=hash_password("InvestigatorPass123!"),
            role_id=role_investigator.id,
        ),
        User(
            username="operator1",
            email="operator1@forensicshield.local",
            hashed_password=hash_password("OperatorPass123!"),
            role_id=role_operator.id,
        ),
        User(
            username="viewer1",
            email="viewer1@forensicshield.local",
            hashed_password=hash_password("ViewerPass123!"),
            role_id=role_viewer.id,
        ),
    ]

    db.add_all(users)
    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    print("[+] Database initialized & seeded successfully with default roles and users.")
    db.close()

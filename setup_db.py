"""Initialize database and create admin user."""

from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.contract import Contract
from app.services.auth_service import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create admin user if not exists
existing = db.query(User).filter(User.email == "alex@finanz-surfer.de").first()
if not existing:
    admin = User(
        email="alex@finanz-surfer.de",
        password_hash=hash_password("admin1234"),
        full_name="Alexander Schack",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("Admin-User erstellt: alex@finanz-surfer.de / admin1234")
else:
    print("Admin-User existiert bereits.")

db.close()
print("Datenbank initialisiert.")

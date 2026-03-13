from app.db.database import SessionLocal
from app.db.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total users: {len(users)}")
for u in users:
    print(f"User: {u.username}, Role: {u.role}")
db.close()

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def seed():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("adminpassword123"),
                user_role="admin"
            )
            db.add(admin)
            print("Created default admin user: admin / adminpassword123")
        else:
            print("Admin user already exists.")

        # Check if customer exists
        customer = db.query(User).filter(User.username == "customer").first()
        if not customer:
            customer = User(
                username="customer",
                password_hash=hash_password("customerpassword123"),
                user_role="customer"
            )
            db.add(customer)
            print("Created default customer user: customer / customerpassword123")
        else:
            print("Customer user already exists.")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()


from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin'

    if not User.query.filter_by(username=username).first():
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"User '{username}' created successfully.")
    else:
        print(f"User '{username}' already exists.")

from app import app, db
from app.models import User

with app.app_context():
    db.create_all()
    user = User(username='admin', email='admin@example.com')
    user.set_password('admin')
    db.session.add(user)
    db.session.commit()

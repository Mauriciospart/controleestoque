from app import app, db
from app.models import User

with app.app_context():
    db.create_all()
    user = User(username='admin', email='admin@example.com', role='Administrador')
    try:
        user.set_password('Admin@1234')
    except ValueError as e:
        print(e)
    else:
        db.session.add(user)
        db.session.commit()

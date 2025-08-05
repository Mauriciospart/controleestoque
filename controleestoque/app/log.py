from app import db
from app.models import Log
from flask_login import current_user

def add_log(action):
    log = Log(user_id=current_user.id, action=action)
    db.session.add(log)
    db.session.commit()

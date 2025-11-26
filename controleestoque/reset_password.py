import os
from app import create_app, db
from app.models import User

# Crie uma instância do aplicativo para configurar o contexto
app = create_app()

# Use o contexto da aplicação para interagir com o banco de dados
with app.app_context():
    # Encontre o usuário 'admin'
    user = User.query.filter_by(username='admin').first()

    if user:
        # Defina a nova senha
        new_password = 'new_password'  # Troque para uma senha temporária segura
        user.set_password(new_password)

        # Salve a alteração no banco de dados
        db.session.commit()

        print(f"A senha do usuário '{user.username}' foi redefinida para '{new_password}'.")
        print("Faça login com esta senha e altere-a imediatamente através do seu perfil.")
    else:
        print("Usuário 'admin' não encontrado no banco de dados.")

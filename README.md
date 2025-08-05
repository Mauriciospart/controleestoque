# Controle de Estoque

## Configuração

Para configurar a aplicação, crie um arquivo `.env` na raiz do projeto com as seguintes variáveis de ambiente:

```
export FLASK_APP=run.py
export SECRET_KEY='your-secret-key'
export MAIL_SERVER='smtp.googlemail.com'
export MAIL_PORT=587
export MAIL_USE_TLS=true
export MAIL_USERNAME='your-email@gmail.com'
export MAIL_PASSWORD='your-password'
export MAIL_DEFAULT_SENDER='your-email@gmail.com'
```

Em seguida, execute os seguintes comandos:

```
pip install -r controleestoque/requirements.txt
flask db upgrade
```

from flask import Flask
from flask_mail import Mail
from .routes import main
import openai
import os
from dotenv import load_dotenv

mail = Mail()  # Criação do objeto global

def create_app():
    app = Flask(__name__)

    # Carrega variáveis de ambiente do .env
    load_dotenv()

    # Configuração da API OpenAI
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Configurações do Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # seu email
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # sua senha ou app password
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

    mail.init_app(app)

    # Blueprint
    app.register_blueprint(main)

    return app

    
    
    
    
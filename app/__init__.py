# -*- coding: utf-8 -*-
import os
from flask import Flask
from .routes import main
from .extensions import mail
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Application Factory para criar e configurar a instância do Flask."""
    app = Flask(__name__, instance_relative_config=True) # Habilita config relativa à instância

    # --- Configuração --- 
    # Carrega configurações padrão e depois sobrescreve com variáveis de ambiente
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "uma-chave-secreta-padrao-insegura"), # ESSENCIAL para flash/sessions
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() in ["true", "1", "t"],
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME")),
        # Adicionar outras configs se necessário (ex: DATABASE_URL)
    )

    # Validação de configurações essenciais
    if not app.config["SECRET_KEY"] or app.config["SECRET_KEY"] == "uma-chave-secreta-padrao-insegura":
        logger.warning("SECRET_KEY não está definida ou usando valor padrão. Defina uma chave segura em suas variáveis de ambiente!")
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        logger.warning("Credenciais de E-mail (MAIL_USERNAME, MAIL_PASSWORD) não configuradas! O envio de e-mail falhará.")
    if not os.getenv("OPENAI_API_KEY"):
         logger.warning("Chave da API OpenAI (OPENAI_API_KEY) não configurada! A geração de análise falhará.")

    # --- Inicializar Extensões ---
    mail.init_app(app)
    # Inicializar outras extensões aqui (ex: db.init_app(app))

    # --- Registrar Blueprints ---
    app.register_blueprint(main)
    # Registrar outros blueprints aqui

    logger.info("Aplicação Flask criada e configurada.")
    return app


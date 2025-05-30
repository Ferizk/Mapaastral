# -*- coding: utf-8 -*-
from app import create_app
import os

# Cria a instância da aplicação Flask usando a factory
# Passa o objeto de configuração se existir (ex: 'config.ProductionConfig')
# Se não, usará as configurações padrão definidas em create_app
app = create_app()

if __name__ == "__main__":
    # Obtém a porta da variável de ambiente ou usa 5000 como padrão
    port = int(os.environ.get("PORT", 5000))
    # Roda o servidor de desenvolvimento do Flask
    # IMPORTANTE: debug=True NÃO deve ser usado em produção!
    # Em produção, use um servidor WSGI como Gunicorn:
    # gunicorn --bind 0.0.0.0:PORT run:app
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")


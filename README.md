# MapaAstral

Aplicação Flask para geração de mapas astrais psicológicos, PDF e envio por e-mail.

## Requisitos

- Python 3.8+
- Flask
- flatlib
- openai
- reportlab
- flask_sqlalchemy
- flask_mail

## Como rodar

1. Instale as dependências:
   ```
   pip install flask flatlib openai reportlab flask_sqlalchemy flask_mail
   ```
2. Configure as variáveis de ambiente:
   - `OPENAI_API_KEY`
   - `EMAIL_USER`
   - `EMAIL_PASS`
3. Execute o app:
   ```
   python app.py
   ```

# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Email, Regexp, ValidationError
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO
import logging
import re

# Carregar variáveis de ambiente do arquivo .env (para desenvolvimento local)
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar extensões sem app
db = SQLAlchemy()
mail = Mail()

# --- Modelos do Banco de Dados ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    data_nasc = db.Column(db.String(10), nullable=False) # Armazenar como string YYYY-MM-DD
    hora_nasc = db.Column(db.String(5), nullable=False) # Armazenar como string HH:MM
    cidade_origem = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=True) # Latitude pode ser nula se geocoding falhar
    lon = db.Column(db.Float, nullable=True) # Longitude pode ser nula se geocoding falhar
    objetivo = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Usuario {self.nome} ({self.email})>'

# --- Formulários WTForms ---
def validate_hora_nasc(form, field):
    if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", field.data):
        raise ValidationError("Formato de hora inválido. Use HH:MM.")

class MapaForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    data = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    hora = StringField('Hora de Nascimento', validators=[DataRequired(), validate_hora_nasc])
    cidade = StringField('Cidade e País', validators=[DataRequired()], description="Ex: São Paulo, Brasil")
    objetivo = TextAreaField('Objetivo com o Mapa', validators=[DataRequired()])

# --- Funções Auxiliares ---
def get_lat_lon_from_city(city_name):
    """Tenta obter lat/lon de um nome de cidade (placeholder)."""
    # Implementação real usaria uma API de geocoding (ex: Geopy com Nominatim)
    # Por simplicidade, vamos simular ou exigir formato específico por enquanto.
    # Exemplo simples (NÃO USAR EM PRODUÇÃO - requer API real):
    logger.info(f"Tentando obter coordenadas para: {city_name}")
    # Simulando para São Paulo
    if "sao paulo" in city_name.lower():
        logger.info("Coordenadas simuladas para São Paulo.")
        return -23.5505, -46.6333
    logger.warning(f"Não foi possível obter coordenadas para {city_name}. Retornando None.")
    return None, None # Retorna None se não conseguir

def gerar_analise_openai(resumo_elementos, objetivo):
    """Gera análise psicológica usando a API do Gemini."""
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        logger.error("Chave da API Gemini não configurada.")
        raise ValueError("Erro interno do servidor: configuração da API ausente.")

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
Gere uma análise psicológica resumida (máximo 3 parágrafos) com base nos seguintes posicionamentos astrais:
{resumo_elementos}

O foco principal do usuário é: {objetivo}

Use uma linguagem terapêutica, acolhedora e voltada ao autoconhecimento, focando no objetivo informado.
Seja conciso e direto ao ponto para este resumo gratuito.
"""
    try:
        logger.info("Enviando requisição para Gemini...")
        response = model.generate_content(prompt)
        analise = response.text.strip()
        logger.info("Análise recebida do Gemini.")
        return analise

    except Exception as e:
        logger.error(f"Erro ao chamar a API do Gemini: {e}")
        raise ConnectionError("Não foi possível gerar a análise no momento. Tente novamente mais tarde.")

def gerar_pdf_mapa(analise, nome_usuario):
    """Gera um PDF simples com a análise astral."""
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        margin = 72 # Margem de 1 polegada
        text_width = width - 2 * margin

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - margin, f"Mapa Astral Psicológico Resumido - {nome_usuario}")

        # Texto da Análise
        c.setFont("Helvetica", 11)
        text_object = c.beginText(margin, height - margin - 30)
        text_object.setLeading(14) # Espaçamento entre linhas

        lines = simpleSplit(analise, 'Helvetica', 11, text_width)
        for line in lines:
            text_object.textLine(line)
            if text_object.getY() < margin + 30: # Verifica se precisa de nova página
                c.drawText(text_object)
                c.showPage()
                c.setFont("Helvetica", 11)
                text_object = c.beginText(margin, height - margin - 30)
                text_object.setLeading(14)
                
        c.drawText(text_object)
        c.save()
        buffer.seek(0)
        logger.info("PDF gerado com sucesso.")
        return buffer
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        raise RuntimeError("Erro ao gerar o arquivo PDF.")

def enviar_email_com_anexo(destinatario, nome_usuario, pdf_buffer):
    """Envia e-mail com o PDF da análise em anexo."""
    sender_email = os.getenv("MAIL_USERNAME")
    if not sender_email or not os.getenv("MAIL_PASSWORD"):
        logger.error("Credenciais de e-mail não configuradas.")
        raise ValueError("Erro interno do servidor: configuração de e-mail ausente.")

    try:
        msg = Message(
            subject=f"Seu Mapa Astral Psicológico Resumido, {nome_usuario}!",
            sender=sender_email,
            recipients=[destinatario]
        )
        msg.body = f"Olá {nome_usuario},\n\nSegue em anexo seu mapa astral psicológico resumido, focado no seu objetivo.\n\nEsperamos que ele contribua para seu autoconhecimento.\n\nPara uma análise completa e aprofundada, considere nosso plano pago (em breve!).\n\nAtenciosamente,\nEquipe Mapa Astral Psicológico"

        pdf_buffer.seek(0)
        msg.attach(
            f"mapa_astral_{nome_usuario.replace(' ', '_').lower()}.pdf",
            "application/pdf",
            pdf_buffer.read()
        )
        mail.send(msg)
        logger.info(f"E-mail enviado para {destinatario}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {destinatario}: {e}")
        raise ConnectionError("Não foi possível enviar o e-mail no momento. Verifique o endereço ou tente mais tarde.")

# --- Application Factory ---
def create_app(config_object='config.Config'): # Você precisará criar um config.py
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)
    # app.config.from_object(config_object) # Carrega config de um objeto/arquivo

    # Configurações básicas (substituir por config_object idealmente)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-muito-forte-padrao') # ESSENCIAL para WTForms e flash messages
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///usuarios.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    # Verificar configurações essenciais
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        logger.warning("Credenciais de E-mail (MAIL_USERNAME, MAIL_PASSWORD) não configuradas!")
    if not os.getenv('GOOGLE_API_KEY'):
        logger.warning("Chave da API Gemini (GOOGLE_API_KEY) não configurada!")

    # Inicializar extensões com o app
    db.init_app(app)
    mail.init_app(app)

    with app.app_context():
        # Criar tabelas do banco de dados se não existirem
        db.create_all()

        # --- Rotas ---
        @app.route('/', methods=['GET', 'POST'])
        def index():
            form = MapaForm()
            if form.validate_on_submit(): # Valida no POST
                try:
                    nome = form.nome.data
                    email = form.email.data
                    data_str = form.data.data.strftime('%Y-%m-%d')
                    hora_str = form.hora.data
                    cidade_origem = form.cidade.data
                    objetivo = form.objetivo.data

                    logger.info(f"Recebido pedido de mapa para: {email}")

                    # 1. Obter Coordenadas (Simulado - Substituir por Geocoding real)
                    lat, lon = get_lat_lon_from_city(cidade_origem)
                    if lat is None or lon is None:
                        flash(f"Não foi possível encontrar as coordenadas para '{cidade_origem}'. Verifique o nome da cidade e país.", 'error')
                        return render_template('index.html', form=form)

                    # 2. Salvar dados do usuário (opcional, mas bom para histórico)
                    usuario = Usuario(
                        nome=nome, email=email, data_nasc=data_str, hora_nasc=hora_str,
                        cidade_origem=cidade_origem, lat=lat, lon=lon, objetivo=objetivo
                    )
                    db.session.add(usuario)
                    db.session.commit()
                    logger.info(f"Usuário {email} salvo no banco de dados.")

                    # 3. Calcular Mapa Astral com flatlib
                    dt = Datetime(f"{data_str} {hora_str}", '+0:00') # Assumindo UTC por enquanto, idealmente calcular TZ
                    pos = GeoPos(lat, lon)
                    chart = Chart(dt, pos)
                    elementos = []
                    for obj in chart.objects(): # Simplificado, pode pegar planetas específicos
                        elementos.append(f"{obj.id} em {obj.sign} ({obj.signlon:.2f}°) na casa {obj.house}")
                    resumo_elementos = '\n'.join(elementos)
                    logger.info("Mapa astral calculado.")

                    # 4. Gerar Análise com Gemini
                    analise = gerar_analise_openai(resumo_elementos, objetivo)

                    # 5. Gerar PDF
                    pdf_buffer = gerar_pdf_mapa(analise, nome)

                    # 6. Enviar E-mail
                    enviar_email_com_anexo(email, nome, pdf_buffer)

                    flash('Seu mapa astral resumido foi gerado e enviado para o seu e-mail!', 'success')
                    return redirect(url_for('index')) # Redireciona para evitar reenvio do form

                except ValidationError as ve:
                    # Erros de validação do WTForms já são tratados pelo template
                    logger.warning(f"Erro de validação no formulário: {ve}")
                    flash("Por favor, corrija os erros no formulário.", 'error')
                except ValueError as ve:
                    logger.error(f"Erro de valor: {ve}")
                    flash(str(ve), 'error')
                except ConnectionError as ce:
                    logger.error(f"Erro de conexão: {ce}")
                    flash(str(ce), 'error')
                except RuntimeError as re:
                     logger.error(f"Erro de runtime: {re}")
                     flash(str(re), 'error')
                except Exception as e:
                    logger.exception(f"Erro inesperado ao processar o formulário: {e}") # Loga o traceback completo
                    flash('Ocorreu um erro inesperado ao processar sua solicitação. Tente novamente mais tarde.', 'error')

            # Renderiza o template no GET ou se a validação falhar no POST
            return render_template('index.html', form=form)

        # Adicionar outras rotas (Sobre, Termos, Política, Contato) aqui
        # Exemplo:
        # @app.route('/sobre')
        # def sobre():
        #     return render_template('sobre.html')

    return app

# O run.py deve ser usado para iniciar a aplicação
# Este bloco if __name__ == '__main__': pode ser removido ou mantido para debug local simples
if __name__ == '__main__':
    app_instance = create_app()
    # Roda em modo debug APENAS para desenvolvimento local
    # Para produção, use um servidor WSGI como Gunicorn ou Waitress
    app_instance.run(debug=True, host='0.0.0.0', port=5001) # Usar porta diferente para evitar conflito

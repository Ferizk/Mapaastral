# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, flash, redirect, url_for
import google.generativeai as genai
import os
from flask_mail import Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from io import BytesIO
from app.extensions import mail
import logging

# Configurar logger
logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

# --- Funções Auxiliares Refatoradas com Tratamento de Erros ---

def gerar_relatorio_resumido(dados):
    """Gera relatório resumido via Gemini com tratamento de erros."""
    logger.info(f"Iniciando geração de relatório para: {dados.get('email')}")
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        logger.error("Chave da API Gemini não configurada.")
        raise ValueError("Erro interno: Configuração da API ausente.")
    genai.configure(api_key=gemini_api_key)

    # Diagnóstico: listar modelos disponíveis
    for m in genai.list_models():
        print("Modelo disponível:", m.name)

    # Use o nome exato de um modelo listado aqui:
    model = genai.GenerativeModel('models/gemini-1.5-flash')  # Exemplo, ajuste conforme o print

    # Validação básica dos dados de entrada (idealmente usar WTForms)
    required_fields = ["nome", "nascimento", "hora", "cidade", "objetivo"]
    if not all(dados.get(field) for field in required_fields):
        logger.warning("Dados incompletos recebidos para gerar relatório.")
        raise ValueError("Dados incompletos fornecidos.")

    prompt = f"""
    Você é um astrólogo que gera mapas astrais psicológicos resumidos. Baseado nos seguintes dados do usuário:
    Nome: {dados["nome"]}
    Data de nascimento: {dados["nascimento"]}
    Hora: {dados["hora"]}
    Cidade: {dados["cidade"]}
    Objetivo: {dados["objetivo"]}

    Gere um texto claro, sucinto e informativo (máximo 3 parágrafos) que explique as principais características e dicas do mapa astral psicológico focado no objetivo informado.
    Use uma linguagem terapêutica, acolhedora e voltada ao autoconhecimento.
    """

    try:
        logger.info("Enviando requisição para Gemini...")
        response = model.generate_content(prompt)
        texto = response.text.strip()
        logger.info("Relatório recebido da Gemini.")
        return texto
    except Exception as e:
        logger.exception(f"Erro inesperado ao chamar a API da Gemini: {e}")
        raise ConnectionError("Não foi possível gerar a análise no momento. Tente novamente mais tarde.")

def criar_pdf(texto, nome_usuario):
    """Cria PDF com o texto da análise, tratando erros."""
    logger.info(f"Iniciando criação de PDF para {nome_usuario}")
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        margin = 72
        text_width = width - 2 * margin

        # Título
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2.0, height - margin, f"Mapa Astral Psicológico Resumido - {nome_usuario}")

        # Texto da Análise
        c.setFont("Helvetica", 11)
        text_object = c.beginText(margin, height - margin - 30)
        text_object.setLeading(14)

        lines = simpleSplit(texto, "Helvetica", 11, text_width)
        for line in lines:
            text_object.textLine(line)
            if text_object.getY() < margin + 30:
                c.drawText(text_object)
                c.showPage()
                c.setFont("Helvetica", 11)
                text_object = c.beginText(margin, height - margin - 30)
                text_object.setLeading(14)

        c.drawText(text_object)
        c.save()
        buffer.seek(0)
        logger.info("PDF criado com sucesso.")
        return buffer
    except Exception as e:
        logger.exception(f"Erro ao criar PDF: {e}")
        raise RuntimeError("Erro interno ao gerar o arquivo PDF.")

def enviar_email_mapa(dados, pdf_buffer):
    """Envia e-mail com o PDF anexo, tratando erros."""
    destinatario = dados.get("email")
    nome_usuario = dados.get("nome")
    objetivo = dados.get("objetivo")
    sender_email = os.getenv("MAIL_USERNAME")

    if not destinatario or not nome_usuario:
        logger.error("Dados insuficientes (email ou nome) para enviar e-mail.")
        raise ValueError("Faltam informações para enviar o e-mail.")

    if not sender_email or not os.getenv("MAIL_PASSWORD"):
        logger.error("Credenciais de e-mail não configuradas.")
        raise ValueError("Erro interno: Configuração de e-mail ausente.")

    logger.info(f"Tentando enviar e-mail para {destinatario}")
    try:
        msg = Message(
            subject=f"Seu Mapa Astral Psicológico Resumido, {nome_usuario}!",
            sender=sender_email,
            recipients=[destinatario]
        )
        msg.body = f"Olá {nome_usuario},\n\nSegue em anexo seu mapa astral psicológico resumido, focado no seu objetivo: {objetivo}.\n\nEsperamos que ele contribua para seu autoconhecimento.\n\nPara uma análise completa e aprofundada, considere nosso plano pago (em breve!).\n\nNamastê 🙏"

        pdf_buffer.seek(0)
        msg.attach(
            f"mapa_astral_{nome_usuario.replace(' ', '_').lower()}.pdf",
            "application/pdf",
            pdf_buffer.read()
        )
        mail.send(msg)
        logger.info(f"E-mail enviado com sucesso para {destinatario}")
    except Exception as e:
        logger.exception(f"Erro ao enviar e-mail para {destinatario}: {e}")
        raise ConnectionError("Não foi possível enviar o e-mail no momento. Verifique o endereço ou tente mais tarde.")

# --- Rotas ---

@main.route("/")
def home():
    """Renderiza a página inicial com o formulário."""
    return render_template("index.html")

@main.route("/gerar_mapa", methods=["POST"])
def gerar_mapa():
    """Processa o formulário, gera análise, PDF e envia e-mail."""
    dados = {
        "nome": request.form.get("nome", "").strip(),
        "nascimento": request.form.get("data"), # Nome do campo no HTML original
        "hora": request.form.get("hora"),
        "cidade": request.form.get("cidade", "").strip(),
        "email": request.form.get("email", "").strip(),
        "objetivo": request.form.get("objetivo", "").strip(),
    }

    # Validação básica (reforçar com WTForms é o ideal)
    if not all(dados.values()):
        flash("Todos os campos são obrigatórios.", "error")
        # Re-renderiza o formulário com os dados preenchidos (se possível)
        # Idealmente, WTForms faria isso automaticamente
        return render_template("index.html", form_data=dados)

    try:
        # 1. Gerar relatório com Gemini
        texto_analise = gerar_relatorio_resumido(dados)

        # 2. Criar PDF
        pdf_buffer = criar_pdf(texto_analise, dados["nome"])

        # 3. Enviar por e-mail
        enviar_email_mapa(dados, pdf_buffer)

        # 4. Redirecionar para página de confirmação com mensagem de sucesso
        flash(f"Sucesso! Seu mapa astral resumido foi enviado para {dados['email']}. Verifique sua caixa de entrada (e spam).", "success")
        return redirect(url_for("main.confirmacao", nome=dados["nome"], objetivo=dados["objetivo"], email=dados["email"])) # Passa dados para a página de confirmação

    except (ValueError, ConnectionError, RuntimeError) as e:
        # Erros esperados (configuração, API, etc.)
        flash(str(e), "error")
        logger.error(f"Erro ao processar /gerar_mapa para {dados.get('email')}: {e}")
    except Exception as e:
        # Erros inesperados
        flash("Ocorreu um erro inesperado ao processar sua solicitação. Tente novamente mais tarde.", "error")
        logger.exception("Erro inesperado em /gerar_mapa para %s: %s", dados.get('email'), e)

    # Se ocorrer erro, re-renderiza o formulário inicial
    # Mantendo os dados preenchidos seria ideal (com WTForms)
    return render_template("index.html", form_data=dados)

@main.route("/confirmacao")
def confirmacao():
    """Exibe a página de confirmação após o envio."""
    # Recebe dados via query string (do redirect)
    nome = request.args.get("nome", "")
    objetivo = request.args.get("objetivo", "")
    email = request.args.get("email", "")
    return render_template("confirmacao.html", nome=nome, objetivo=objetivo, email=email)

# Adicionar rotas para Sobre, Termos, Política, Contato aqui
# Exemplo:
# @main.route("/sobre")
# def sobre():
#     return render_template("sobre.html") # Necessário criar o template sobre.html

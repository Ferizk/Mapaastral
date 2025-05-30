from flask import Blueprint, render_template, request
import openai
from flask_mail import Message
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import current_app
from app import mail  # certifique-se de que o objeto 'mail' esteja importado do app/__init__.py

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

def gerar_relatorio_resumido(dados):
    prompt = f"""
    Você é um astrólogo que gera mapas astrais psicológicos resumidos. Baseado nos seguintes dados do usuário:
    Nome: {dados['nome']}
    Data de nascimento: {dados['nascimento']}
    Hora: {dados['hora']}
    Cidade: {dados['cidade']}
    Objetivo: {dados['objetivo']}

    Gere um texto claro, sucinto e informativo com cerca de meia página que explique as principais características e dicas do mapa astral psicológico focado no objetivo informado.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # ou "gpt-4o-mini", conforme plano
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.7,
    )
    texto = response['choices'][0]['message']['content']
    return texto

def criar_pdf(texto):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    y = 800
    for linha in texto.split('\n'):
        p.drawString(50, y, linha.strip())
        y -= 15
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buffer.seek(0)
    return buffer

@main.route("/gerar_mapa", methods=["POST"])
def gerar_mapa():
    dados = {
        "nome": request.form.get("nome"),
        "nascimento": request.form.get("nascimento"),
        "hora": request.form.get("hora"),
        "cidade": request.form.get("cidade"),
        "email": request.form.get("email"),
        "objetivo": request.form.get("objetivo"),
    }

    print("Email recebido:", dados["email"])

    # 1. Gerar relatório
    texto = gerar_relatorio_resumido(dados)

    # 2. Criar PDF
    pdf = criar_pdf(texto)

    # 3. Enviar por e-mail
    msg = Message(
        subject="Seu Mapa Astral Psicológico Resumido",
        recipients=[dados["email"]],
        body=f"Olá {dados['nome']},\n\nSegue em anexo seu mapa astral psicológico focado em {dados['objetivo']}.\n\nNamastê 🙏"
    )
    msg.attach("Mapa_Astral_Resumido.pdf", "application/pdf", pdf.read())
    mail.send(msg)

    # 4. Mostrar página de confirmação
    return render_template("confirmacao.html", email=dados["email"], nome=dados["nome"], objetivo=dados["objetivo"])

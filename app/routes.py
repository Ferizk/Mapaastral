from flask import Blueprint, render_template, request

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/gerar_mapa", methods=["POST"])
def gerar_mapa():
    nome = request.form.get("nome")
    nascimento = request.form.get("nascimento")
    hora = request.form.get("hora")
    cidade = request.form.get("cidade")
    email = request.form.get('email')
    print("Email recebido:", email)  # Só para testar
    
    return f"<h2>Olá, {nome}!</h2><p>Você nasceu em {cidade} no dia {nascimento} às {hora}.</p>"

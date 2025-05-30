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

    # Aqui você deve chamar sua função que gera o mapa e envia o email (não incluída aqui)

    return render_template("confirmacao.html", email=email)

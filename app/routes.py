from flask import Blueprint, render_template, request

main = Blueprint('main', __name__)

@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@main.route("/gerar_mapa", methods=["POST"])
def gerar_mapa():
    nome = request.form.get("nome")
    data = request.form.get("data")
    hora = request.form.get("hora")
    cidade = request.form.get("cidade")
    objetivo = request.form.get("objetivo")
    
    # Aqui você vai processar e gerar o PDF depois
    return f"Mapa astral gerado para {nome}, objetivo: {objetivo}"
 

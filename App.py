from flask import Flask, render_template_string, request, send_file
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import openai
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Configurações do banco de dados e email
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

db = SQLAlchemy(app)
mail = Mail(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Column(db.String(100)))
    email = db.Column(db.String(100))
    data = db.Column(db.String(20))
    hora = db.Column(db.String(20))
    cidade = db.Column(db.String(50))
    objetivo = db.Column(db.Text)

FORM_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mapa Astral Psicológico</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-indigo-100 to-purple-200 min-h-screen flex items-center justify-center p-6">
  <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-xl">
    <h2 class="text-2xl font-bold text-center text-indigo-800 mb-6">Mapa Astral com Foco Psicológico</h2>
    <form method="POST" class="space-y-4">
      <input name="nome" placeholder="Nome" class="w-full p-3 rounded-xl border border-gray-300" required>
      <input name="email" type="email" placeholder="Seu e-mail" class="w-full p-3 rounded-xl border border-gray-300" required>
      <input type="date" name="data" class="w-full p-3 rounded-xl border border-gray-300" required>
      <input type="time" name="hora" class="w-full p-3 rounded-xl border border-gray-300" required>
      <input name="cidade" placeholder="Cidade (lat,long) - Ex: -23.5505,-46.6333" class="w-full p-3 rounded-xl border border-gray-300" required>
      <input name="objetivo" placeholder="Objetivo psicológico" class="w-full p-3 rounded-xl border border-gray-300" required>
      <button type="submit" class="w-full bg-indigo-600 text-white py-3 rounded-xl hover:bg-indigo-700 transition">Gerar Mapa</button>
    </form>
    {% if resultado %}
    <div class="mt-6 bg-indigo-50 p-4 rounded-xl">
      <h3 class="text-lg font-semibold text-indigo-700">Resultado:</h3>
      <pre class="text-sm mt-2 whitespace-pre-wrap">{{ resultado }}</pre>
      <a href="/download" class="inline-block mt-4 text-indigo-600 underline">Baixar PDF</a>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

resultado_global = ""

@app.route('/', methods=['GET', 'POST'])
def gerar_mapa():
    global resultado_global
    resultado = None
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        data = request.form['data']
        hora = request.form['hora']
        lat, lon = request.form['cidade'].split(',')
        objetivo = request.form['objetivo']

        usuario = Usuario(nome=nome, email=email, data=data, hora=hora, cidade=f"{lat},{lon}", objetivo=objetivo)
        db.session.add(usuario)
        db.session.commit()

        dt = Datetime(data, hora, '+0:00')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)

        elementos = []
        for obj in chart.objects():
            elementos.append(f"{obj} em {obj.sign} na casa {obj.house}")

        resumo = '\n'.join(elementos)

        prompt = f"""
        Gere uma análise psicológica profunda com base nos seguintes posicionamentos astrais:
        {resumo}
        Objetivo do usuário: {objetivo}
        Use uma linguagem terapêutica, acolhedora e voltada ao autoconhecimento.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        resultado = response['choices'][0]['message']['content']
        resultado_global = resultado
        gerar_pdf(resultado)
        enviar_email(email)

    return render_template_string(FORM_HTML, resultado=resultado)

@app.route('/download')
def download():
    return send_file("mapa_psicologico.pdf", as_attachment=True)

def gerar_pdf(texto):
    c = canvas.Canvas("mapa_psicologico.pdf", pagesize=letter)
    width, height = letter
    text_object = c.beginText(40, height - 40)
    text_object.setFont("Helvetica", 12)

    for linha in texto.split('\n'):
        text_object.textLine(linha)

    c.drawText(text_object)
    c.showPage()
    c.save()

def enviar_email(destinatario):
    with app.app_context():
        msg = Message(subject="Seu Mapa Astral Psicológico", sender=app.config['MAIL_USERNAME'], recipients=[destinatario])
        msg.body = "Segue em anexo seu mapa astral psicológico. Esperamos que ele contribua para seu autoconhecimento."
        with open("mapa_psicologico.pdf", "rb") as f:
            msg.attach("mapa_psicologico.pdf", "application/pdf", f.read())
        mail.send(msg)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

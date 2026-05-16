from flask import Flask, render_template  # Agrega render_template aquí

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # Cambia esto para que cargue el HTML

if __name__ == "__main__":
    app.run(debug=True)

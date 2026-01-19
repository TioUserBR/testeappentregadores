from flask import Flask, render_template, request, redirect, jsonify
import json, os, datetime

app = Flask(__name__)
ARQ = "pedidos.json"

def carregar():
    if not os.path.exists(ARQ):
        return []
    with open(ARQ, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(dados):
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

@app.route("/")
def atendente():
    pedidos = [p for p in carregar() if p["status"] == "pendente"]
    return render_template("index.html", pedidos=pedidos)

@app.route("/enviar", methods=["POST"])
def enviar():
    dados = carregar()

    novo = {
        "id": int(datetime.datetime.now().timestamp()),
        "cliente": request.form["cliente"],
        "endereco": request.form["endereco"],
        "ferramenta": request.form["ferramenta"],
        "quantidade": request.form["quantidade"],
        "status": "pendente",
        "hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    dados.append(novo)
    salvar(dados)
    return redirect("/")

@app.route("/entregador")
def entregador():
    pedidos = [p for p in carregar() if p["status"] == "pendente"]
    return render_template("entregador.html", pedidos=pedidos)

@app.route("/pegar/<int:id>")
def pegar(id):
    dados = carregar()
    for p in dados:
        if p["id"] == id:
            p["status"] = "pego"
    salvar(dados)
    return redirect("/entregador")

@app.route("/pego")
def pegos():
    pedidos = [p for p in carregar() if p["status"] == "pego"]
    return render_template("pego.html", pedidos=pedidos)

if __name__ == "__main__":
    app.run(debug=True)

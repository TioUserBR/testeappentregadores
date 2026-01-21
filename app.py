# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO
import json
import os
import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

ARQ = "pedidos.json"


# ======================
# Utilidades
# ======================

def carregar():
    if not os.path.exists(ARQ):
        return []
    try:
        with open(ARQ, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def salvar(dados):
    try:
        with open(ARQ, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print("Erro ao salvar:", e)


def agora_data():
    return datetime.datetime.now().strftime("%d/%m/%Y")


def agora_hora():
    return datetime.datetime.now().strftime("%H:%M:%S")


# ======================
# Rotas principais
# ======================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/atendente")
def atendente():
    todos = carregar()
    pendentes = [p for p in todos if p.get("status") == "pendente"]
    return render_template("index.html", pedidos=pendentes)


@app.route("/entregador")
def entregador():
    todos = carregar()
    pendentes = [p for p in todos if p.get("status") == "pendente"]
    return render_template("entregador.html", pedidos=pendentes)


@app.route("/pego")
def pegos():
    todos = carregar()
    pegos = [p for p in todos if p.get("status") == "pego"]
    return render_template("pego.html", pedidos=pegos)


# ======================
# Ações
# ======================

@app.route("/enviar", methods=["POST"])
def enviar():
    dados = carregar()

    novo_pedido = {
        "id": int(datetime.datetime.now().timestamp() * 1000),
        "cliente": request.form.get("cliente", "").strip(),
        "endereco": request.form.get("endereco", "").strip(),
        "ferramenta": request.form.get("ferramenta", "").strip(),
        "quantidade": request.form.get("quantidade", "1").strip(),
        "status": "pendente",
        "data": agora_data(),
        "hora": agora_hora()
    }

    dados.append(novo_pedido)
    salvar(dados)

    socketio.emit("novo_pedido", novo_pedido)

    return redirect("/atendente")


@app.route("/pegar/<int:id>")
def pegar(id):
    dados = carregar()

    for p in dados:
        if p.get("id") == id and p.get("status") == "pendente":
            p["status"] = "pego"
            salvar(dados)
            socketio.emit("pedido_atualizado", {"id": id, "status": "pego"})
            break

    return redirect("/entregador")


@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    dados = carregar()
    cliente = request.form.get("cliente", "").strip()
    endereco = request.form.get("endereco", "").strip()

    for p in dados:
        if p.get("id") == id:
            if cliente:
                p["cliente"] = cliente
            if endereco:
                p["endereco"] = endereco

            salvar(dados)
            socketio.emit("pedido_atualizado", {
                "id": id,
                "cliente": cliente,
                "endereco": endereco
            })
            return jsonify({"success": True})

    return jsonify({"success": False}), 404


@app.route("/apagar/<int:id>", methods=["POST"])
def apagar(id):
    dados = carregar()
    novo = [p for p in dados if p.get("id") != id]

    if len(novo) != len(dados):
        salvar(novo)
        socketio.emit("pedido_apagado", {"id": id})
        return jsonify({"success": True})

    return jsonify({"success": False}), 404


@app.route("/api/novos_pedidos")
def novos_pedidos():
    dados = carregar()
    pendentes = [p for p in dados if p.get("status") == "pendente"]
    return jsonify(pendentes)


# ======================
# Inicialização
# ======================

if __name__ == "__main__":
    # Local (PC / Android)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

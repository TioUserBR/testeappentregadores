from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, emit
import json
import os
import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ARQ = "pedidos.json"


def carregar():
    if not os.path.exists(ARQ):
        return []
    try:
        with open(ARQ, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []  # evita crash se o arquivo estiver corrompido


def salvar(dados):
    try:
        with open(ARQ, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar pedidos: {e}")


@app.route("/")
def atendente():
    todos_pedidos = carregar()
    pedidos_pendentes = [
        p for p in todos_pedidos
        if p.get("status") == "pendente"
    ]
    return render_template("index.html", pedidos=pedidos_pendentes)


@app.route("/enviar", methods=["POST"])
def enviar():
    dados = carregar()

    novo_pedido = {
        "id": int(datetime.datetime.now().timestamp() * 1000),  # mais precisão
        "cliente": request.form.get("cliente", "").strip(),
        "endereco": request.form.get("endereco", "").strip(),
        "ferramenta": request.form.get("ferramenta", "").strip(),
        "quantidade": request.form.get("quantidade", "1").strip(),
        "status": "pendente",
        "hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    dados.append(novo_pedido)
    salvar(dados)

    # Notifica todos os conectados (entregadores, etc)
    socketio.emit("novo_pedido", novo_pedido)

    return redirect("/")


@app.route("/entregador")
def entregador():
    todos_pedidos = carregar()
    pedidos_pendentes = [
        p for p in todos_pedidos
        if p.get("status") == "pendente"
    ]
    return render_template("entregador.html", pedidos=pedidos_pendentes)


@app.route("/pegar/<int:id>")
def pegar(id):
    dados = carregar()
    pedido_encontrado = False

    for p in dados:
        if p.get("id") == id and p.get("status") == "pendente":
            p["status"] = "pego"
            pedido_encontrado = True
            break

    if pedido_encontrado:
        salvar(dados)
        socketio.emit("pedido_atualizado", {"id": id, "status": "pego"})

    return redirect("/entregador")


@app.route("/api/novos_pedidos")
def novos_pedidos():
    dados = carregar()
    pendentes = [p for p in dados if p.get("status") == "pendente"]
    return jsonify(pendentes)


@app.route("/pego")
def pegos():
    todos_pedidos = carregar()
    pedidos_pegos = [
        p for p in todos_pedidos
        if p.get("status") == "pego"
    ]
    return render_template("pego.html", pedidos=pedidos_pegos)

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    dados = carregar()
    novo_cliente = request.form.get("cliente", "").strip()
    novo_endereco = request.form.get("endereco", "").strip()

    atualizado = False
    for p in dados:
        if p.get("id") == id:
            if novo_cliente:
                p["cliente"] = novo_cliente
            if novo_endereco:
                p["endereco"] = novo_endereco
            atualizado = True
            break

    if atualizado:
        salvar(dados)
        socketio.emit("pedido_atualizado", {"id": id, "cliente": novo_cliente, "endereco": novo_endereco})
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Pedido não encontrado"}), 404

@app.route("/apagar/<int:id>", methods=["POST"])
def apagar(id):
    dados = carregar()
    dados_antigos = len(dados)
    
    dados = [p for p in dados if p.get("id") != id]
    
    if len(dados) < dados_antigos:
        salvar(dados)
        socketio.emit("pedido_apagado", {"id": id})
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Pedido não encontrado"}), 404
        
if __name__ == "__main__":
    # Rode em 0.0.0.0 para ser acessível fora do localhost (ex: Termux, celular, rede local)
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True  # necessário em algumas versões recentes do Flask
    )
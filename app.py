from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO
import psycopg2
import os
import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE_URL = os.environ.get("DATABASE_URL")

# ------------------------
# Banco
# ------------------------

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id BIGINT PRIMARY KEY,
            cliente TEXT,
            endereco TEXT,
            ferramenta TEXT,
            quantidade TEXT,
            status TEXT,
            hora TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def buscar_pedidos(status=None):
    conn = get_conn()
    cur = conn.cursor()

    if status:
        cur.execute("SELECT * FROM pedidos WHERE status=%s ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM pedidos ORDER BY id DESC")

    rows = cur.fetchall()
    cur.close()
    conn.close()

    pedidos = []
    for r in rows:
        pedidos.append({
            "id": r[0],
            "cliente": r[1],
            "endereco": r[2],
            "ferramenta": r[3],
            "quantidade": r[4],
            "status": r[5],
            "hora": r[6],
        })
    return pedidos

# ------------------------
# Rotas
# ------------------------

@app.route("/")
def atendente():
    pedidos = buscar_pedidos("pendente")
    return render_template("index.html", pedidos=pedidos)

@app.route("/enviar", methods=["POST"])
def enviar():
    conn = get_conn()
    cur = conn.cursor()

    pid = int(datetime.datetime.now().timestamp() * 1000)

    pedido = {
        "id": pid,
        "cliente": request.form.get("cliente"),
        "endereco": request.form.get("endereco"),
        "ferramenta": request.form.get("ferramenta"),
        "quantidade": request.form.get("quantidade"),
        "status": "pendente",
        "hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    cur.execute("""
        INSERT INTO pedidos VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        pedido["id"], pedido["cliente"], pedido["endereco"],
        pedido["ferramenta"], pedido["quantidade"],
        pedido["status"], pedido["hora"]
    ))

    conn.commit()
    cur.close()
    conn.close()

    socketio.emit("novo_pedido", pedido)

    return redirect("/")

@app.route("/entregador")
def entregador():
    pedidos = buscar_pedidos("pendente")
    return render_template("entregador.html", pedidos=pedidos)

@app.route("/pegar/<int:id>")
def pegar(id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("UPDATE pedidos SET status='pego' WHERE id=%s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    socketio.emit("pedido_atualizado", {"id": id, "status": "pego"})

    return redirect("/entregador")

@app.route("/pego")
def pegos():
    pedidos = buscar_pedidos("pego")
    return render_template("pego.html", pedidos=pedidos)

@app.route("/api/novos_pedidos")
def novos_pedidos():
    pedidos = buscar_pedidos("pendente")
    return jsonify(pedidos)

# ------------------------

if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000)

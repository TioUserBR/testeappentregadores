import os
from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# -------------------- DB --------------------

def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL não configurada")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id SERIAL PRIMARY KEY,
        cliente TEXT NOT NULL,
        endereco TEXT NOT NULL,
        hora TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        id SERIAL PRIMARY KEY,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        nome TEXT NOT NULL,
        qtd INTEGER NOT NULL
    );
    """)

    db.commit()
    db.close()

init_db()

# -------------------- FUNÇÕES --------------------

def carregar_pedidos(status):
    db = get_db()
    c = db.cursor(cursor_factory=RealDictCursor)

    c.execute("SELECT * FROM pedidos WHERE status=%s ORDER BY id DESC", (status,))
    pedidos_raw = c.fetchall()

    pedidos = []

    for p in pedidos_raw:
        c.execute("SELECT nome, qtd FROM itens WHERE pedido_id=%s", (p["id"],))
        itens = c.fetchall()

        pedidos.append({
            "id": p["id"],
            "cliente": p["cliente"],
            "endereco": p["endereco"],
            "hora": p["hora"],
            "itens": itens
        })

    db.close()
    return pedidos

# -------------------- HOME (DASHBOARD) --------------------

@app.route("/")
def home():
    db = get_db()
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'")
    pendentes = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM pedidos WHERE status='pego'")
    pegos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM pedidos")
    total = c.fetchone()[0]

    db.close()

    return render_template(
        "home.html",
        pendentes=pendentes,
        pegos=pegos,
        total=total
    )

# -------------------- TELAS --------------------

@app.route("/atendente")
def atendente():
    pedidos = carregar_pedidos("pendente")
    return render_template("index.html", pedidos=pedidos)

@app.route("/entregador")
def entregador():
    pedidos = carregar_pedidos("pendente")
    return render_template("entregador.html", pedidos=pedidos)

@app.route("/pego")
def pego():
    pedidos = carregar_pedidos("pego")
    return render_template("pego.html", pedidos=pedidos)

# -------------------- NOVO PEDIDO --------------------

@app.route("/enviar", methods=["POST"])
def enviar():
    cliente = request.form.get("cliente")
    endereco = request.form.get("endereco")

    ferramentas = request.form.getlist("ferramenta[]")
    quantidades = request.form.getlist("quantidade[]")

    hora = datetime.now().strftime("%d/%m/%Y %H:%M")

    db = get_db()
    c = db.cursor()

    c.execute("""
        INSERT INTO pedidos (cliente, endereco, hora, status)
        VALUES (%s,%s,%s,'pendente') RETURNING id
    """, (cliente, endereco, hora))

    pedido_id = c.fetchone()[0]

    itens_socket = []

    for nome, qtd in zip(ferramentas, quantidades):
        if nome.strip():
            c.execute("""
                INSERT INTO itens (pedido_id, nome, qtd)
                VALUES (%s,%s,%s)
            """, (pedido_id, nome, int(qtd)))

            itens_socket.append({"nome": nome, "qtd": int(qtd)})

    db.commit()
    db.close()

    socketio.emit("novo_pedido", {
        "id": pedido_id,
        "cliente": cliente,
        "endereco": endereco,
        "itens": itens_socket
    })

    return redirect("/atendente")

# -------------------- PEGAR --------------------

@app.route("/pegar/<int:id>")
def pegar(id):
    db = get_db()
    c = db.cursor()

    c.execute("UPDATE pedidos SET status='pego' WHERE id=%s", (id,))

    db.commit()
    db.close()

    socketio.emit("pedido_atualizado", {"id": id})

    return redirect("/entregador")

# -------------------- EDITAR --------------------

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    cliente = request.form.get("cliente")
    endereco = request.form.get("endereco")

    db = get_db()
    c = db.cursor()

    c.execute("""
        UPDATE pedidos SET cliente=%s, endereco=%s WHERE id=%s
    """, (cliente, endereco, id))

    db.commit()
    db.close()

    return jsonify(success=True)

# -------------------- APAGAR --------------------

@app.route("/apagar/<int:id>", methods=["POST"])
def apagar(id):
    db = get_db()
    c = db.cursor()

    c.execute("DELETE FROM pedidos WHERE id=%s", (id,))

    db.commit()
    db.close()

    return jsonify(success=True)

# -------------------- MAIN --------------------

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

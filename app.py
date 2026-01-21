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
app.config["SECRET_KEY"] = "segredo"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    ping_interval=25,
    ping_timeout=60
)

# ---------------- DB ----------------

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    db = get_db()
    c = db.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id SERIAL PRIMARY KEY,
        cliente TEXT,
        endereco TEXT,
        hora TEXT,
        status TEXT
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        id SERIAL PRIMARY KEY,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        nome TEXT,
        qtd INTEGER
    );
    """)
    db.commit()
    db.close()

init_db()

# ---------------- FUNÇÕES ----------------

def carregar_pedidos(status):
    db = get_db()
    c = db.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM pedidos WHERE status=%s ORDER BY id DESC", (status,))
    pedidos_raw = c.fetchall()
    pedidos = []
    for p in pedidos_raw:
        c.execute("SELECT nome,qtd FROM itens WHERE pedido_id=%s", (p["id"],))
        itens = c.fetchall()
        p["itens"] = itens
        pedidos.append(p)
    db.close()
    return pedidos

# ---------------- ROTAS ----------------

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
    return render_template("home.html", pendentes=pendentes, pegos=pegos, total=total)

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
        INSERT INTO pedidos (cliente,endereco,hora,status)
        VALUES (%s,%s,%s,'pendente') RETURNING id
    """, (cliente,endereco,hora))
    pedido_id = c.fetchone()[0]

    itens_socket = []
    for nome,qtd in zip(ferramentas,quantidades):
        if nome.strip():
            c.execute("INSERT INTO itens (pedido_id,nome,qtd) VALUES (%s,%s,%s)",
                      (pedido_id,nome,int(qtd)))
            itens_socket.append({"nome":nome,"qtd":int(qtd)})

    db.commit()
    db.close()

    socketio.emit("novo_pedido", {
        "id": pedido_id,
        "cliente": cliente,
        "endereco": endereco,
        "itens": itens_socket
    }, broadcast=True)

    return redirect("/atendente")

@app.route("/pegar/<int:id>")
def pegar(id):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE pedidos SET status='pego' WHERE id=%s", (id,))
    db.commit()
    db.close()

    socketio.emit("pedido_atualizado", {"id": id}, broadcast=True)
    return redirect("/entregador")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    cliente = request.form.get("cliente")
    endereco = request.form.get("endereco")
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE pedidos SET cliente=%s,endereco=%s WHERE id=%s",
              (cliente,endereco,id))
    db.commit()
    db.close()
    return jsonify(success=True)

@app.route("/apagar/<int:id>", methods=["POST"])
def apagar(id):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM pedidos WHERE id=%s",(id,))
    db.commit()
    db.close()
    return jsonify(success=True)

# ---------------- MAIN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)


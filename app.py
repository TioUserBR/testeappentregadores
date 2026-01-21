<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Painel Principal | Sistema de Coletas</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
:root {
  --primary:#2563eb;
  --success:#16a34a;
  --warning:#f59e0b;
  --bg:#f1f5f9;
  --card:#ffffff;
  --text:#0f172a;
  --muted:#64748b;
  --radius:18px;
}

*{box-sizing:border-box;font-family:'Plus Jakarta Sans',sans-serif;}

body{
  margin:0;
  background:var(--bg);
  color:var(--text);
}

header{
  background:#fff;
  padding:16px 24px;
  border-bottom:1px solid #e5e7eb;
  display:flex;
  justify-content:space-between;
  align-items:center;
}

header h1{
  margin:0;
  font-size:18px;
  color:var(--primary);
}

.container{
  padding:24px;
  max-width:1300px;
  margin:auto;
}

.cards{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:20px;
  margin-bottom:24px;
}

.card-info{
  background:var(--card);
  padding:20px;
  border-radius:var(--radius);
  box-shadow:0 6px 18px rgba(0,0,0,.05);
  display:flex;
  justify-content:space-between;
  align-items:center;
}

.card-info span{
  font-size:13px;
  color:var(--muted);
}

.card-info strong{
  font-size:26px;
}

.btns{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:16px;
  margin-bottom:30px;
}

.btn{
  padding:16px;
  border-radius:14px;
  background:var(--primary);
  color:#fff;
  text-decoration:none;
  text-align:center;
  font-weight:700;
  box-shadow:0 4px 12px rgba(37,99,235,.25);
}

.btn.secondary{background:#0ea5e9;}
.btn.success{background:var(--success);}

.charts{
  display:grid;
  grid-template-columns:2fr 1fr;
  gap:20px;
}

@media(max-width:900px){
  .charts{grid-template-columns:1fr;}
}

.chart-box{
  background:#fff;
  border-radius:var(--radius);
  padding:16px;
  height:320px;
  box-shadow:0 6px 18px rgba(0,0,0,.05);
}

canvas{
  width:100%!important;
  height:100%!important;
}
</style>
</head>
<body>

<header>
  <h1>📦 Sistema de Coletas</h1>
  <span style="color:#64748b;font-size:14px;">Dashboard</span>
</header>

<div class="container">

  <!-- CARDS -->
  <div class="cards">
    <div class="card-info">
      <div>
        <span>Pendentes</span><br>
        <strong style="color:var(--warning)">{{ pendentes }}</strong>
      </div> ⏳
    </div>

    <div class="card-info">
      <div>
        <span>Coletados</span><br>
        <strong style="color:var(--success)">{{ pegos }}</strong>
      </div> ✅
    </div>

    <div class="card-info">
      <div>
        <span>Total</span><br>
        <strong>{{ total }}</strong>
      </div> 📊
    </div>
  </div>

  <!-- BOTÕES -->
  <div class="btns">
    <a href="/atendente" class="btn">👨‍💼 Painel Atendente</a>
    <a href="/entregador" class="btn secondary">🚚 Painel Entregador</a>
    <a href="/pego" class="btn success">📁 Itens Coletados</a>
  </div>

  <!-- GRÁFICOS -->
  <div class="charts">
    <div class="chart-box">
      <h3>📈 Pedidos por Status</h3>
      <canvas id="graficoBarra"></canvas>
    </div>

    <div class="chart-box">
      <h3>🥧 Distribuição</h3>
      <canvas id="graficoPizza"></canvas>
    </div>
  </div>

</div>

<script>
const pendentes = {{ pendentes }};
const pegos = {{ pegos }};

new Chart(document.getElementById("graficoBarra"),{
  type:"bar",
  data:{
    labels:["Pendentes","Coletados"],
    datasets:[{
      data:[pendentes,pegos],
      backgroundColor:["#f59e0b","#16a34a"]
    }]
  },
  options:{
    responsive:true,
    maintainAspectRatio:false
  }
});

new Chart(document.getElementById("graficoPizza"),{
  type:"doughnut",
  data:{
    labels:["Pendentes","Coletados"],
    datasets:[{
      data:[pendentes,pegos],
      backgroundColor:["#f59e0b","#16a34a"]
    }]
  },
  options:{
    responsive:true,
    maintainAspectRatio:false
  }
});
</script>

</body>
</html>

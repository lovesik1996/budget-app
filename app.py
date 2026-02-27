from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "budget.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,          -- 'income' albo 'expense'
        amount_grosz INTEGER NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        date TEXT NOT NULL           -- YYYY-MM-DD
    )
    """)
    conn.commit()
    conn.close()

def grosze(text):
    # zamienia "12,34" albo "12.34" na 1234
    t = text.strip().replace(",", ".")
    zl = float(t)
    return int(round(zl * 100))

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Budżet</title>
  <style>
    body { font-family: system-ui; margin: 16px; }
    .card { padding: 12px; border: 1px solid #ddd; border-radius: 12px; margin-bottom: 12px; }
    input, select { width: 100%; padding: 10px; margin-top: 6px; margin-bottom: 10px; border-radius: 10px; border: 1px solid #ccc; }
    button { width: 100%; padding: 12px; border-radius: 12px; border: 0; }
    .row { display:flex; gap:10px; }
    .row > div { flex: 1; }
    .neg { color: #c00; }
    .pos { color: #090; }
  </style>
</head>
<body>
  <h2>Budżet (Etap 1)</h2>

  <div class="card">
    <b>Saldo:</b>
    <span class="{{ 'pos' if saldo_grosz>=0 else 'neg' }}">
      {{ "%.2f"|format(saldo_grosz/100) }} zł
    </span>
  </div>

  <div class="card">
    <form method="post" action="/add">
      <div class="row">
        <div>
          <label>Typ</label>
          <select name="kind">
            <option value="expense">Wydatek</option>
            <option value="income">Przychód</option>
          </select>
        </div>
        <div>
          <label>Data</label>
          <input name="date" value="{{ today }}">
        </div>
      </div>

      <label>Kwota (np. 12,34)</label>
      <input name="amount" placeholder="0,00">

      <label>Kategoria</label>
      <input name="category" placeholder="np. Żywność">

      <label>Opis (opcjonalnie)</label>
      <input name="note" placeholder="np. Biedronka">

      <button type="submit">Dodaj</button>
    </form>
  </div>

  <div class="card">
    <b>Ostatnie transakcje</b>
    <ul>
      {% for t in tx %}
        <li>
          {{ t["date"] }} —
          {{ t["category"] }} —
          {% if t["kind"] == "expense" %}
            <span class="neg">-{{ "%.2f"|format(t["amount_grosz"]/100) }} zł</span>
          {% else %}
            <span class="pos">+{{ "%.2f"|format(t["amount_grosz"]/100) }} zł</span>
          {% endif %}
          {% if t["note"] %} ({{ t["note"] }}){% endif %}
        </li>
      {% endfor %}
    </ul>
  </div>
</body>
</html>
"""

@app.get("/")
def index():
    conn = db()
    tx = conn.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC LIMIT 30").fetchall()
    saldo = conn.execute("""
        SELECT COALESCE(SUM(CASE WHEN kind='income' THEN amount_grosz ELSE -amount_grosz END), 0) AS s
        FROM transactions
    """).fetchone()["s"]
    conn.close()
    return render_template_string(TEMPLATE, tx=tx, saldo_grosz=saldo, today=datetime.now().strftime("%Y-%m-%d"))

@app.post("/add")
def add():
        kind = request.form.get("kind", "expense")
        amount = request.form.get("amount", "0")
        category = request.form.get("category", "Inne").strip() or "Inne"
        note = request.form.get("note", "").strip()
        date = request.form.get("date", datetime.now().strftime("%Y-%m-%d")).strip()

        conn = db()
        conn.execute(
        "INSERT INTO transactions(kind, amount_grosz, category, note, date) VALUES (?,?,?,?,?)",
        (kind, grosze(amount), category, note, date)
    )
        conn.commit()
        conn.close()
        init_db()
        return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
0
0


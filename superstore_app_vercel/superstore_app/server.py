"""Local API + static server. Run: python server.py  ->  http://localhost:8000  (needs only Python 3, no packages)"""
import json, sqlite3, os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
HERE = os.path.dirname(os.path.abspath(__file__)); DB = os.path.join(HERE, "superstore.db")
def connect(): return sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
M = {"sales": "SUM(sales)", "profit": "SUM(profit)", "quantity": "SUM(quantity)"}

def q(con, sql, a=()):
    cur = con.execute(sql, a); cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

def where(p, year=True):
    w, a = ["1=1"], []
    for k in ("market", "category", "segment"):
        if p.get(k, "All") != "All": w.append(f"{k}=?"); a.append(p[k])
    if year and p.get("year", "All") != "All": w.append("year=?"); a.append(int(p["year"]))
    if p.get("search"): w.append("(product_name LIKE ? OR customer_name LIKE ?)"); a += [f"%{p['search']}%"] * 2
    return " AND ".join(w), a

def dashboard(p):
    con = connect(); m = p.get("metric", "sales"); m = m if m in M else "sales"
    n = max(1, min(int(p.get("n", 10)), 50)); days = int(p.get("days", 90)); W, A = where(p); W2, A2 = where(p, False)
    mx = con.execute("select max(order_date) from sales").fetchone()[0]
    k = q(con, f"""select ifnull(sum(sales),0) sales, ifnull(sum(profit),0) profit, ifnull(sum(quantity),0) units,
        count(distinct order_id) orders, count(distinct customer_id) customers,
        count(distinct case when returned=1 then order_id end) returned from sales where {W}""", A)[0]
    grp = lambda col: q(con, f"select {col} name, sum(sales) sales, sum(profit) profit, sum(quantity) quantity from sales where {W} group by {col} order by sales desc", A)
    top = lambda key, name, extra: q(con, f"select {key} id, {name} name, {extra} sum(sales) sales, sum(profit) profit, sum(quantity) quantity, count(distinct order_id) orders from sales where {W} group by {key} order by {M[m]} desc limit {n}", A)
    inactive = q(con, f"""select customer_id id, customer_name name, segment, max(order_date) last_order, sum(sales) lifetime,
        count(distinct order_id) orders, cast(julianday(?)-julianday(max(order_date)) as int) days_inactive
        from sales where {W2} group by customer_id having days_inactive>=? order by {'lifetime desc' if p.get('sort','v')=='v' else 'days_inactive desc'}""", [mx] + A2 + [days])
    total_c = q(con, f"select count(distinct customer_id) c from sales where {W2}", A2)[0]["c"]
    return dict(max_date=mx, kpi=k, trend=q(con, f"select ym name, sum(sales) sales, sum(profit) profit, sum(quantity) quantity from sales where {W} group by ym order by ym", A),
        category=grp("category"), market=grp("market"), segment=grp("segment"),
        products=top("product_id", "product_name", "sub_category sub,"), customers=top("customer_id", "customer_name", "segment,"),
        losers=q(con, f"select product_name name, sub_category sub, sum(sales) sales, sum(profit) profit from sales where {W} group by product_id order by profit asc limit {n}", A),
        inactive=inactive[:200], inactive_total=len(inactive), inactive_value=sum(x["lifetime"] for x in inactive), customer_total=total_c)

class H(SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=HERE, **k)
    def do_GET(s):
        u = urlparse(s.path)
        if u.path.startswith("/api/"):
            p = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/api/meta":
                    con = connect(); d = {c: [r[0] for r in con.execute(f"select distinct {c} from sales order by 1")] for c in ("year", "market", "category", "segment")}
                else: d = dashboard(p)
                b = json.dumps(d).encode(); s.send_response(200)
            except Exception as e: b = json.dumps({"error": str(e)}).encode(); s.send_response(500)
            s.send_header("Content-Type", "application/json"); s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
        else: super().do_GET()
    def log_message(s, *a): pass

if __name__ == "__main__":
    print("Dashboard running at http://localhost:8000  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()

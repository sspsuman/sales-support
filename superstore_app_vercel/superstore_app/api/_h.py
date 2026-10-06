import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

def make(fn):
    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            p = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            try: body, code = json.dumps(fn(p)).encode(), 200
            except Exception as e: body, code = json.dumps({"error": str(e)}).encode(), 500
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "public, s-maxage=3600, stale-while-revalidate")
            self.end_headers(); self.wfile.write(body)
    return handler

def meta(_):
    con = server.connect()
    return {c: [r[0] for r in con.execute(f"select distinct {c} from sales order by 1")] for c in ("year", "market", "category", "segment")}

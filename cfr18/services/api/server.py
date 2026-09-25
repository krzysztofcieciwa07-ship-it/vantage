import json,os
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
Q=Path(os.getenv("QUEUE_FILE","/data/queue.jsonl")); EVENTS=Path(os.getenv("EVENTS_FILE","/data/events.jsonl"))
def emit(e):
 EVENTS.parent.mkdir(parents=True,exist_ok=True)
 with EVENTS.open("a") as f:f.write(json.dumps(e)+"\n")
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=="/health": self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
  self.send_response(404); self.end_headers()
 def do_POST(self):
  if self.path!="/enqueue": self.send_response(404); self.end_headers(); return
  n=int(self.headers.get("Content-Length","0")); item=json.loads(self.rfile.read(n)); item.setdefault("status","queued")
  Q.parent.mkdir(parents=True,exist_ok=True)
  with Q.open("a") as f:f.write(json.dumps(item)+"\n")
  emit({"event":"enqueued","id":item["id"]})
  self.send_response(202); self.end_headers()
HTTPServer(("0.0.0.0",8098),H).serve_forever()

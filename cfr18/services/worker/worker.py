import json,os,time
from pathlib import Path
Q=Path(os.getenv("QUEUE_FILE","/data/queue.jsonl")); EVENTS=Path(os.getenv("EVENTS_FILE","/data/events.jsonl")); PROCESSED=Path(os.getenv("PROCESSED_FILE","/data/processed.jsonl"))
VAR=os.getenv("FAULT_VARIANT","double_process"); CRASH_MS=int(os.getenv("CRASH_AFTER_MS","250")); DEDUP=os.getenv("DEDUP","0")=="1"
def emit(e):
 EVENTS.parent.mkdir(parents=True,exist_ok=True)
 with EVENTS.open("a") as f:f.write(json.dumps(e)+"\n")
seen=set(); started=time.monotonic()
while True:
 if Q.exists():
  lines=Q.read_text().splitlines()
  for idx,raw in enumerate(lines):
   if idx in seen: continue
   try:item=json.loads(raw)
   except: seen.add(idx); continue
   jid=item["id"]
   if DEDUP and PROCESSED.exists() and any(json.loads(x).get("id")==jid for x in PROCESSED.read_text().splitlines()): seen.add(idx); continue
   emit({"event":"processing","id":jid,"variant":VAR})
   time.sleep(CRASH_MS/1000)
   if VAR=="double_process" and time.monotonic()-started > 0.15 and os.getenv("CRASH_ONCE","1")=="1":
    emit({"event":"crash","id":jid}); os._exit(137)
   PROCESSED.parent.mkdir(parents=True,exist_ok=True)
   with PROCESSED.open("a") as f:f.write(json.dumps({"id":jid,"status":"done"})+"\n")
   emit({"event":"done","id":jid}); seen.add(idx)
 time.sleep(.1)

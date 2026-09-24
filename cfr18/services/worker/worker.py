import json,os,time
from pathlib import Path
Q=Path(os.getenv("QUEUE_FILE","/data/queue.jsonl")); Q.parent.mkdir(parents=True,exist_ok=True)
seen=0
while True:
    if Q.exists():
        lines=Q.read_text().splitlines()
        if len(lines)>seen: seen=len(lines)
    time.sleep(.25)

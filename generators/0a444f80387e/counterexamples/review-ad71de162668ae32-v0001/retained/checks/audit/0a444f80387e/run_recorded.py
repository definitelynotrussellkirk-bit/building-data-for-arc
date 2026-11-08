"""Run one public audit command and retain its exact receipt."""
import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
name=sys.argv[1]
args=sys.argv[2:]
cwd=Path.cwd()
p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
log=root/(name+'.log')
log.write_text(p.stdout)
receipt=root/'COMMANDS.json'
records=json.loads(receipt.read_text()) if receipt.exists() else []
records.append({'argv':args,'cwd':str(cwd),'exit_code':p.returncode,'evidence_paths':[str(log.relative_to(cwd/'WORK'))]})
receipt.write_text(json.dumps(records,indent=2)+'\n')
print(p.stdout)
raise SystemExit(p.returncode)

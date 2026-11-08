# Workspace

`reference_probe.py` is an independent, input-only mirror for the panel count
rule plus portable canonical-data helpers. It never imports the selected Racket
source.

`qualify.py` is the fast handoff probe. It checks every advertised exact
override in every difficulty band, verifies that the central-3x3 shortcut fits
all canonical pairs but fails a generated border witness, and exhaustively
rotates the query over consecutive four-pair windows for requested cyclic
starts.

From the packet root:

```bash
python3 run_with_racket.py python3 generators/7017b91a367d/workspace/qualify.py \
  --starts 12 --out ../checks/qualify-final.json
```

This tool supplements the Racket-backed battery and lesson census; it does not
replace either authority check.

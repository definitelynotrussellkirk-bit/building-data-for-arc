# Review workspace for `dd3fa537fa22`

`reference_probe.py` is an independent object parser, Python authority mirror,
and shortcut probe. It deliberately does not reuse generator parsing or output
code, so it can catch shared implementation errors.

From the packet root, after Racket setup:

```sh
python3 run_with_racket.py python3 generators/dd3fa537fa22/workspace/reference_probe.py \
  --generated 12 --out ../checks/reference-probe.json
```

The report verifies every canonical oracle label, checks that both declared
canonical-fitting rivals (`horizontal_order` and `area_then_horizontal`) really
fit all canonical pairs, and records whether generated profiles refute them.
Task-local tests import the same independent functions from the staged workspace.

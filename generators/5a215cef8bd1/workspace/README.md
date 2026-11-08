# Workspace

The selected implementation is `../generator.py`. Workspace tools are reviewer aids and are never selected as label authority.

## `reference_probe.py`

Independent structural/oracle probe for task `5a215cef8bd1`. It:

- reads canonical pairs through the public `reviewer_support` helper;
- implements a separate Python rendition of the compact transform-panel rule;
- checks canonical agreement, deterministic generation, self-check cleanliness, template-size/layout/control-order coverage, and transformed-cell conservation;
- evaluates the canonical-fitting `fixed_3x3_panel` shortcut;
- optionally executes the selected canonical Racket program and compares outputs.

From the packet root, with the supplied Racket runtime prepared:

```sh
python3 run_with_racket.py python3 generators/5a215cef8bd1/workspace/reference_probe.py \
  --count 250 --out ../checks/reference-probe.json --racket
```

The final retained run covered 750 generated inputs and 28 Racket parity cases. The probe is evidence and debugging support, not a replacement for authoritative Racket labels.

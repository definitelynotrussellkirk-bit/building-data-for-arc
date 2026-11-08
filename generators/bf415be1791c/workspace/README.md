# Workspace tools

The selected implementation is `../generator.py`; workspace scripts are review tools and are never selected automatically.

## `probe_shortcuts.py`

Source-bound probe for the generator's declared `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`. It verifies canonical fit, materializes the deterministic 7/2/1 witness, checks every fixed schedule/query rotation, and emits generator/rule hashes plus exact outputs.

Example from the packet root:

```bash
python3 run_with_racket.py python3 generators/bf415be1791c/workspace/probe_shortcuts.py \
  --out generators/bf415be1791c/counterexamples/component-selection/probe.json
```

## `probe_component_selectors.py`

Independent bounded hypothesis search. It derives magenta components directly from grids and enumerates size thresholds, contiguous size ranges, rank selectors, and total/component-count gates. It intentionally does not use the declared rival registry, allowing it to detect omitted rival classes.

Example from the packet root:

```bash
python3 run_with_racket.py python3 generators/bf415be1791c/workspace/probe_component_selectors.py \
  --out ../checks/second-pass/component-selector-family-probe.json
```

The output distinguishes a refuted/ambiguous candidate from one that never disagrees on the measured schedule. This finite family search is not a proof against arbitrary programs.

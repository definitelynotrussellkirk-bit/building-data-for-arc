# Workspace tools

## Canonical curriculum probe

`curriculum_probe.py` reads the selected generator's live shortcut/lesson registries, verifies claimed canonical shortcuts, enumerates four-pair cyclic windows and holds out each pair once. Its independent centroid-angle Python labels are diagnostics anchored to the canonical pairs; Racket remains production authority.

From the **outer packet extraction directory**:

```bash
python3 review.py run python3 generators/5bba6e671cec/workspace/curriculum_probe.py --seeds 30 --starts 8 --out ../checks/curriculum-probe.json
```

Use the local environment's Python when dependencies are isolated. The wrapper payload runs from `WORK/repo`. The probe exits nonzero for a failed canonical premise, profile coverage, generation/scoring error, or a rival fitting all three demos and differing on a held-out query. No undeclared-rule completeness claim is implied.

## Proposed parametric audit and replay

`parametric/rotation.py` implements episode-level direction/step settings using exact instantiated Racket programs and exports solver-safe public challenges separately from private author evidence. Its `audit` and `rescore` commands validate live rival bindings, source/asset hashes, deterministic inputs, exact labels and all query holdouts. See [parametric/README.md](parametric/README.md) for commands, parameters, evidence format and limitations. This extension is a prototype; it does not replace the canonical authority or confer training approval.

# Native parametric prototype: repeated domino completion

This prototype preserves task `a286b2610efc`'s exact canonical program as the
private default setting and adds one nearby, episode-fixed alternative:

- `{"rounds": 1}` — execute the canonical simultaneous completion pass once.
- `{"rounds": 2}` — execute that same pass twice.

The second setting has a real sequential dependency. Step A applies one pass to
the original input and produces an input-dependent intermediate grid. Step B
scans that intermediate, so newly completed length-three/four segments can enable
new writes that were not available in the original input. A one-pass
counterfactual therefore changes the final output on the retained causal case.

## Episode contract

`promotion.json` declares 2–6 demonstrations, 1–4 queries, three demonstrations
for native qualification, and four materialized training queries. Inputs are
independent of the private setting and are prefix-stable across independently
requested counts. The sampler schedules all four boundaries, all four quadrants,
both orientations, interior two-sided cases, isolated singleton distractors,
and canvases through a substantive 30×30 fourth query.

The public projection is one query at a time. Visible bytes contain only all
training input/output pairs and the current query input. Settings, seed, program,
query answer, future inputs, private order, and total query count stay private.
`evidence/current/private-export-map.json` is controller-side metadata and must
never be exposed to the model.

## Files

- `adapter.py` — deterministic native adapter and Python claim mirror.
- `canonical.rkt` — byte-exact canonical default program.
- `promotion.json` — finite adapter contract.
- `audit.py` — bounded protected-Racket self-audit and public/private checks.
- `evidence/current/` — protected execution, finite-rival, boundary, canonical,
  and projection evidence.
- `evidence/manifest.json` — source-bound author-reported inventory.

## Reproduce

From the packet's outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/a286b2610efc/tests/test_native_parametric.py -q
python3 review.py run python3 \
  generators/a286b2610efc/workspace/parametric/audit.py \
  --out generators/a286b2610efc/workspace/parametric/evidence/FRESH
python3 review.py run python3 -m arcpuzzles parametric qualify a286b2610efc \
  --out ../checks/a286b2610efc/qualification --summary
```

The retained audit is finite: it checks six plausible executable rival families,
two protected-Racket seeds at demo counts 2/3/6, a 12-seed Python construction
census, canonical parity, and four min/max boundary shapes. It is not a proof of
universal uniqueness, measured training value, owner acceptance, or training
admission. The owner must replay native qualification and acceptance on the exact
integrated bytes.

# Reusable review probes for 99e7ba062bec

Run from the extracted packet root unless noted.

## Full admission battery

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 99e7ba062bec \
  --battery --timeout 4000 --phase after --out ../checks/after
```

Interpret the battery summary, not only the final shell code. Required high-value stages are `defect_lint`, `dist_gate`, `profile_floor`, `semantic_gate`, and `override`.

## Focused Python regressions

Run from `repo`:

```bash
python3 -m pytest -q generators/99e7ba062bec/tests/test_generator_99e7ba062bec.py
```

These regressions check canonical parity, role-linked palette, exact profile, transform discrimination, seven-branch schedule coverage, five-demo rival separation, exact overrides, mutation rejection, determinism, fresh returned grids, and global-RNG purity.

## Semantic contract only

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 99e7ba062bec \
  --stage semantic_gate --phase after --out ../checks/semantic
```

Expected: strict 600/600, canonical 5/5, seven witnesses firing, all declared rival claims verified, and all sampled lessons identifiable.

## Override contract only

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 99e7ba062bec \
  --stage override --phase after --out ../checks/override
```

Expected: all accepted draws exactly reproduce requested `command`, `a_active_count`, and `c_active_count`; unknown keys and out-of-domain values are rejected.

## What not to weaken

- Do not collapse A/B/C to one color; that makes color preservation unlearnable.
- Do not add anti-transpose; it is absent from the authority.
- Do not replace exhaustive shape filtering with a fallback that can return a symmetric mask.
- Do not require generated transform uniqueness of canonical inputs; canonical tie cases use first-match semantics.
- Do not raise `EXAMPLES_NEEDED` above five without a serializer contract change.

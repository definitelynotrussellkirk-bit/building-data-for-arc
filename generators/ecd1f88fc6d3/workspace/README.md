# Directed-ray review tools

These tools belong to the selected generator; they do not automatically change its approval or catalog mapping. No network access is needed once the packet's Racket setup is complete. Run the following from the extracted packet root after applying the delta. Their outputs go under `checks/` and must not overwrite evidence you need to preserve.

## Distribution and authority probe

```bash
python3 run_with_racket.py python3 generators/ecd1f88fc6d3/workspace/probe_distribution.py --out ../checks/reprobe.json --racket
```

Reports source hash, normalized layout support, code-blind rival agreement, exact counterexamples and actual Racket outputs. Works in the native repository and a properly materialized runtime. `--seeds N` controls per-profile draws. `--generator PATH` loads a frozen predecessor without modifying it; the returned before/after evidence already records the compared hashes. Default-band probes are a fixed 10 seeds × 12 sample indices per band, independent of `--seeds`.

## Dimensions/profiles/bands stress

```bash
python3 repo/generators/ecd1f88fc6d3/workspace/stress_generation.py --out checks/restress.json
```

Checks 3,600 draws, 900 scheduled distractor refutations, 144 replays and process-global RNG state. This is local invariant/Python evidence, not Racket parity; keep the separate Racket probe or full battery. Run without Python's `-O`: assertions are deliberate test failures. The corpus SHA supports independent replay comparisons.

## Relocated verification

```bash
python3 run_with_racket.py python3 generators/ecd1f88fc6d3/workspace/verify_portable.py --runtime ../.review/fresh-portable --out ../checks/fresh-portable
```

Both destinations must be new. Builds the official standalone runtime, overlays this task's new tests/probe explicitly, checks source identity/no symlinks and runs the 40 task tests and Racket probe there with sanitized child environment. Requires the API, pytest and Racket supplied/used by this packet. The result records the actual runtime and exact subprocess commands. Full review runtimes are not included in the delta ZIP.

## Read-only assigned audit reproducer

```bash
python3 run_with_racket.py python3 generators/ecd1f88fc6d3/workspace/audit_probe.py --out ../checks/reaudit.json
```

Checks only `cdc2954e8f80` and `7bba59d92716`; needs the full native packet because those sources are not in the selected task's standalone runtime. It neither edits audit targets nor substitutes for their full batteries. Saves generated samples, ignored override calls and Racket-verified distinguishing inputs.

## Main regression and battery commands

```bash
python3 -m pytest -q repo/generators/ecd1f88fc6d3/tests
python3 run_with_racket.py python3 -m arcpuzzles check ecd1f88fc6d3 --battery --timeout 4000 --phase after --out ../checks/recheck
```

`HANDOFF.md` gives scope and next-step priorities. The solve-phase `solve/probe_visible.py` is separate and uses only the visible challenge; do not merge reference-bearing review tools into a future blind solve workflow.

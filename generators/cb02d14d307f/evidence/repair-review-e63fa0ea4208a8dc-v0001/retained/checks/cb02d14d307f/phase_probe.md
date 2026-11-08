# cb02d14d307f: bounded phase ambiguity witness

Outcome: a concrete generated three-demonstration/one-query episode admits a simple wrong phase rule. This does **not** establish ambiguity in the canonical task: four of its five training examples reject this rival.

The canonical rule starts copying source row zero at the first blank row below the visible pattern: source index `(r - start) mod source_rows`. The rival keeps the cycle phased to the top of the entire grid: `r mod source_rows`. It differs by one expression in the canonical Racket program. The generator's current `SUMMARY` and `SUMMARY.md` describe the rival's absolute-row formula, which makes this a particularly plausible misreading. No production source or summary was edited.

The probe screens at most seeds 0 through 127 for a default episode consisting of sample indices 0, 1, 2 as demonstrations and 3 as query. It stops at seed **87**. All generated inputs pass the selected generator's `self_check`, and use its defaults without overrides. Each demonstration has two source rows and repeat-band start row four, so both phase rules agree. The query has four source rows and repeat-band start row six, exposing the two-row phase shift.

Protected Racket executes both exact programs on all four generated inputs and all six canonical input/output pairs: **20 evaluations**. Results: rival fit on the generated episode is `[true, true, true, false]`; the canonical program matches all six canonical labels; the rival matches only canonical training example 3 (zero-based), and does not match the canonical query.

Evidence is bound to generator SHA-256 `dbbc244ef602de119b2be9faedb621851dab03e2abb09ecd91824515b5ce82a3` and canonical-program SHA-256 `29152d0edbe6338e84e9d348a2743830dc3a92e8d5bbf1972bb5fb050fa7ff2f`. The JSON includes protected-runtime identity, exact rival program, full demonstration/query inputs and both outputs.

## Reproduction

From the packet directory:

```sh
WORK/.venv/bin/python review.py run python3 /workspace/scratch/3c6e3daf4d86/packet/WORK/checks/cb02d14d307f/phase_probe.py
```

Observed exit code: **0**. The wrapper runs the payload with the repository as cwd. Output: `WORK/checks/cb02d14d307f/phase_probe_report.json`.

Scope: one rival, one replayed generated episode, no broad battery or parametric qualification. The seed search screened phase arithmetic and stopped on its first candidate; this is an existence witness, not a rate estimate. No current `review_index.json` existed in the assigned generator home. No other peer or MAIN source was reviewed.

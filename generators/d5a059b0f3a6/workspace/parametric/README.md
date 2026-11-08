# Proposed `mirror_mode` parametric prototype

This task-local prototype leaves the production generator and canonical authority unchanged. It chooses one hidden setting once per episode:

- `single_axis` — canonical/default: infer each frame's missing axis and mirror only across it.
- `both_axes` — proposed: use the same frames, seeds and distractor removal, but complete every seed across both frame axes and the 180-degree orbit.

The object roles, corner-frame detection, blue seed semantics, and removal of external blue distractors stay fixed. Only the executed completion law changes. Every generated pair is required to distinguish the two settings. The default episode contains **3 demonstrations and 4 distinct queries** under one setting.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/d5a059b0f3a6/workspace/parametric/verify.py \
  --seed 20261023 \
  --out ../checks/parametric/verification.json \
  --artifact-dir ../checks/parametric/artifacts
```

The verifier executes both exact Racket programs on every demonstration and query, checks them against the Python authoring mirror, requires demonstrations to refute the rival setting, requires all four queries to remain setting-sensitive, and writes answer-free public challenges with filenames derived only from their visible content.

Public export is deliberately two-phase. The verifier first redacts and names every challenge, rejects visible-name collisions, then emits public files in lexicographic visible-filename order. Reversing the private setting enumeration therefore does not change public creation order; the setting-to-filename mapping remains only in the private manifest.

Scope: proposed bounded authoring evidence only. It is not catalog approval, production API integration, proof that these two settings exhaust all plausible hypotheses, or a claim that every possible storage side channel has been eliminated.

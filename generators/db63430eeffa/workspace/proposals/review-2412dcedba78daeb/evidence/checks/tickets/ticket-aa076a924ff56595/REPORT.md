# Allocation-quality audit — ticket-aa076a924ff56595

Status: **completed**. The pinned seed
`90812138d50be7410c0829b67e9ac166c3ddcb883867180b69a17fd6b6329b9b`
selects three records by
`random.Random(int(seed, 16)).sample(sorted(PACKET-MANIFEST.json["all_ids"]), 3)`:
`7147e98f8173`, `747486860e56`, and `7195f447bb20`.
All source hashes match the packet manifest. The exact machine-readable inspection,
paths, source pins, policy counts, cost assumptions, and limits are in `report.json`.

## Actual pools and weights

The packet has 154 `main_ids`. Its normal authoring pool contains 152 approved
original-family generators missing parameter extensions. An independent SHA-256
roll reserves 1/10 of authoring draws for 120 public-evaluation anchors; only one
anchor currently has a related generator, so the other 119 are inspired-extension
assignments. These are authoring probabilities, not dataset mixture weights.

All three sampled catalog rows have `mix_weight: 1.0`, despite materially different
states:

- `7147e98f8173` is approved/reviewed-safe and has six exact axes, one task-test
  file, a seven-demonstration lesson, and a current unresolved semantic-gate audit:
  its declared `corner_fixed_vector` canonical shortcut does not fit every labeled
  canonical pair. It has no retained parameter prototype.
- `747486860e56` is approved/reviewed-safe with four task-test files, a six-demo
  production lesson, and a reviewer-reported two-setting triangle-leg prototype.
  That prototype is explicitly unapproved, has no production parameter API, and
  covers two three-demo/one-query episodes, four distinct inputs, and 50 retained
  Racket evaluations—not four-query supervision.
- `7195f447bb20` is unapproved/unverified, has no task tests or finite-rival lesson
  contract, and retains a reproduced unresolved teaching gap: 900 draws produced
  no predecessor/successor-guard witness although the canonical rule requires the
  guard. It also has no parameter prototype.

None of the three belongs to the 152-ID normal authoring pool, so this uniform
catalog sample diagnoses evidence heterogeneity; it does **not** estimate the
normal pool's quality rate. No ARC-GEN or RE-ARC record was selected, so this audit
makes no source-quality or volume recommendation for either. Provenance alone is
not quality evidence.

## One bounded executable probe

The ticket's pinned target `703a842c8e24` was executed once through real Racket.
The probe generated one deterministic episode with four demonstrations and four
queries, covering its four scheduled profiles twice. Results:

- 8/8 inputs were distinct and passed `self_check`;
- all four queries were distinct from demonstrations;
- all four queries passed the production demonstration-only `lesson_identifiable`
  gate;
- real Racket matched all four Python-mirror query labels;
- the run used eight logical labels and completed in 5.88 seconds wall time
  (3.12 seconds inside the isolated Racket receipt);
- every one of 35 observed first-body cells was zero, so the retained
  first-body-padding shortcut matched all eight labels.

Thus four-query export is mechanically feasible for this source, but generic
finite-rival success does not clear its current source-specific audit debt. More
volume before repairing or scheduling the retained witness would preserve that
shortcut. The visible-content-addressed public challenge is under `public/`; seed,
program, labels, and the Racket receipt remain in `private_episode.json`.

## Concrete alternative and bounded stopping rule

Preserve the independent 10% public-evaluation focus. For the remaining normal
90%, compare the current 100% approved-original parameter emphasis with a pilot
mix of 70% approved-original parameter work, 20% source-bound known repairs, and
10% evidence-ranked repairs/current prototypes. Using explicitly illustrative,
not sample-fitted assumptions:

| Normal stratum | Share | Qualified-upgrade probability | Review min | Racket min |
| --- | ---: | ---: | ---: | ---: |
| Approved original parameters | 70% | 0.65 | 60 | 10 |
| Original known repairs | 20% | 0.60 | 45 | 8 |
| Other evidence-ranked repairs/prototypes | 10% | 0.50 | 30 | 5 |

The illustrative current rate is 0.65 qualified upgrades per review hour. The
alternative estimates 0.625 upgrades per assignment at 54 review minutes and
9.1 Racket minutes, or 0.694 upgrades per review hour (+6.8%). These numbers are
hypotheses, not measured optima or training-effect estimates.

Run a 30-assignment pilot: 18 approved-parameter, 6 known-repair, 3 other
repair/prototype, and 3 public-evaluation-focus assignments. Measure routine
completion, accepted source-bound upgrades, four distinct Racket-labeled queries,
retained-audit shortcut survival, reviewer minutes, Racket labels, and deduplicated
inputs. After at least three assignments in each non-evaluation stratum, stop
expanding a new stratum if fewer than half are routine-complete or if its median
review time exceeds twice the approved-parameter stratum without at least a 20%
gain in accepted upgrades per 100 Racket labels. Stop immediately on source drift,
label disagreement, hidden-answer exposure, or training-admission leakage.

The dated October 23, 2026 training context reports ARCpuzzles at 37% of
materialized generator tokens but only 7.3% of outputs with side at least 20,
versus 47% in public evaluation. That is older r6 evidence, not a fresh measurement
of this packet. No model job, mixture change, approval change, or training
admission was performed.

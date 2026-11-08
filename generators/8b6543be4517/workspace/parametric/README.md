# Mirror completion and completed-component ranking

This task-local proposed family preserves the exact canonical Racket program in
`mode=closure`. Its alternate `mode=largest_after` first completes the color-7
pattern across the unique full color-8 divider, then discovers four-connected
color-7 components in that completed grid and recolors **all** components of the
global maximum size to color 2. Ties all win, including reflected pairs. Other
components stay 7. The full divider and untouched distractors stay unchanged;
occupied reflection targets become 7 before ranking. Out-of-bounds reflections
are skipped without deleting their source pixels.

The dependency is substantive: imported reflected pixels can join previously
separate fragments **within each half**, changing component membership and size
ranking. The divider prevents connectivity across the axis. Selecting original
components before completion can therefore paint the wrong objects. A diagonal
contact does not merge four-connected components. A clipped one-sided component
can be the global winner; ranking separately within the two sides changes the rule.

## Supported requests and finite teaching scope

`adapter.py` exports `program(settings)` and
`generate(seed, settings, demos, queries)`. Settings must be exactly
`{"mode":"closure"}` or `{"mode":"largest_after"}`. Counts are independent:
2–6 demonstrations and 1–4 queries, with a fixed setting throughout each episode.
Both modes use the same input stream for a matched seed/count request. The family
constructs scenes on 8–30 rows and columns, including a substantive 30×30 fourth
query. Ordinary demonstration geometry is smaller; the family does not claim
every scene profile is available at every dimension. Sampling and teaching search
are bounded and raise on failure rather than duplicating inputs or shortening a
lesson. `sample_input` exposes explicit height, width, orientation and profile
for focused authoring stress cases.

The sampler chooses demonstrations before queries. It rejects demonstrations
that fail to distinguish the declared 11 reflection rivals for closure, or 18
reflection/ranking rivals for the alternate, using diagnostic Python predictions.
These include original-before-completion selection, eight-connectivity, painting
all 7s, smallest components, a single tied winner, and per-side winners. Every
returned gold label comes from protected Racket and is compared with the diagnostic
model. This is finite evidence, not proof of universal uniqueness or learning benefit.
Native qualification independently executes the two setting programs on demonstrations.

## Reproduce the private authoring audit

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/8b6543be4517/workspace/parametric/audit.py \
  --out generators/8b6543be4517/workspace/parametric/evidence/current
```

The payload runs from `WORK/repo` using the bundled protected Racket runtime.
The audit requests both modes at seed 0 with two demonstrations, seed 17 with
three, and seed 97 with six; every episode has four queries. It refuses an
existing destination. On sampling or execution failure it retains a private
summary, completed episodes and tracebacks, then exits nonzero. Choose a fresh
output path for a rerun and update the manifest evidence path accordingly.

`episodes.private.json` retains exact labels, programs, settings, seeds, teaching
checks and runtime identities. `summary.private.json` records source hashes,
the actual command, successful/failed episode counts, grid shapes, per-color
content counts, rival scope and component-rank diagnostics. The first alternate
demonstration also has an executed wrong-intermediate counterfactual in
`counterfactual.private.json`. This authoring receipt is not the qualification-bound
sequential witness. `inspection.private.html` renders exact labeled grids for that
dependency and a 30×30 query; keep it private.

Only `public/` is model-visible. Each file is the exact
`reviewer_support.public_challenge_bytes` projection of visible demonstrations
and the first current query input, named by SHA256 of those exact public bytes.
Names do not incorporate settings, seeds, query labels or ordinals. Future queries,
their answers and the controller mapping live exclusively in `index.private.json`.
The controller reveals the next query only after the preceding answer, without
total-count or final-turn hints. Evaluation can stop after the first answer with
the identical first-turn challenge. Do not share the surrounding audit directory.

## Inventory, native qualification and causal witness

After focused tests and the audit pass, inventory the final source and evidence:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 8b6543be4517 \
  --evidence generators/8b6543be4517/workspace/parametric/evidence/current \
  --reported-checks 'Six bounded protected-Racket episodes; exact checks and limitations in evidence/current/summary.private.json'
python3 review.py run python3 -m arcpuzzles parametric qualify 8b6543be4517 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8b6543be4517/qualification --summary
python3 review.py run python3 -m arcpuzzles.review_witness template \
  --qualification ../checks/8b6543be4517/qualification/qualification.json \
  --out ../checks/8b6543be4517/witness-recipe.json
```

The `--reported-checks` text is an author claim: use it only after that actual
audit succeeds. Include focused tests with manifest `--include` as appropriate.
An existing manifest requires its exact current SHA256 via `--replace`; it never
inherits old passing claims automatically. Finish all source/evidence edits
before inventory and qualification; later changes require refreshed evidence.

Fill the witness recipe's four causal descriptions, actual intermediate value,
ablation and standalone `family.counterfactual_program()` text. Choose the
qualified first alternate demonstration that exhibits the rank inversion. Then:

```bash
python3 review.py run python3 -m arcpuzzles.review_witness build \
  --qualification ../checks/8b6543be4517/qualification/qualification.json \
  --recipe ../checks/8b6543be4517/witness-recipe.json \
  --out ../checks/8b6543be4517/causal
```

Keep qualification and witness outside the inventoried `evidence/current` folder.
Copy the four dependency descriptions into MAIN's `parametric_work` record and
cite the qualification and witness paths in `evidence_paths`. Passing native
qualification supports reviewer status `ready`; exact-source owner admission
remains pending. The owner integrates the delta, verifies the causal argument and
replays both witness programs, then performs fresh qualification and acceptance
on live bytes. For that owner handoff, the native commands are:

```bash
arcpuzzles parametric qualify 8b6543be4517 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/qualification-8b6543be4517 --summary
arcpuzzles parametric accept 8b6543be4517 \
  --qualification var/review/qualification-8b6543be4517/qualification.json \
  --reason 'Reviewed parameter semantics, grammar, protected causal replay and exact-source qualification'
arcpuzzles parametric status 8b6543be4517
```

The review owner's MAIN admission path performs these fresh checks during
integration. Reviewer receipts do not authorize acceptance or training admission.
Accepted status is source-bound; further source/runtime changes require fresh
qualification and acceptance. This family does not modify the canonical generator,
its approval, sampling weights or any training configuration.

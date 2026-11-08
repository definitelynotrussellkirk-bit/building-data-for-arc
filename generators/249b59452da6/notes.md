# Working notes: 249b59452da6

## Review scope and authority

Assignment `review-de3a83533182ed07` starts from imported generator 2.0.1,
SHA-256 `1fa4c790495dfbba0fda57cabae2904b9f20a40dc993730d6fdd2e6ff835341b`.
No earlier review return was used as empirical evidence for these bytes. The
imported summary describes isolated red pairs; its reason for excluding the
canonical distractors and red bars is unknown. Associated historical notes stay
unchanged in `evidence/associated_notes.jsonl`.

The canonical program and ledger remain byte-identical. The selected base
`racket_target.target_code` was aligned exactly to the canonical program because
the authority-sync gate found divergent selected text. Archival `raw_code` stays
unchanged. This is a selected-authority text edit, with no intended semantic
change, and is reported explicitly rather than hidden as generator-only work.

## Defects and decisions

The baseline's random separated placement silently underfilled a 7x7 request for
five pairs in all ten retained seed probes. Advertised dimensions and palette
controls did not describe actual behavior. Its rectangularity-only validator
accepted all 56 destructive mutations in the battery. There were zero canonical
dimension/palette profile hits in 60 draws and no executable teaching contract.

The repair uses exact constructive placement. All axis values are independently
observable from pixels. The compact family enumerates subsets of one checkerboard
parity within a 4x4..4x6 patch, records the actual eligible-window count, and places
every requested color outside protected zero corners. It has a deliberately
bounded support family. Refusals carry the requested tuple; silent truncation,
unbounded placement retries, and broad exception swallowing are rejected.

Ordinary scenes use two full teaching families. Counts two and three combine a
T-shaped red motif with a compact foil; counts four through eight use a red
chain, a tailed zigzag, and optional isolated pairs. The shared foil includes a
nonred diagonal, a nonred-blocked red diagonal, and a three-red-corner near miss.
These constructions preserve both orientations, overlap, boundary conditions,
red attachments, and unchanged distractors without consulting output labels.

An intermediate 3.0.0 candidate passed 11/12 battery stages but had too many
four-connected objects: canonical median 6 lay below its observed 12..21 range.
The dedicated low-count family repaired that support gap. Independent review
also found two undeclared canonical-fitting shortcuts, allowing a third red
corner and rejecting orthogonally attached endpoints. Both are now declared and
refuted by every ordinary scene. The failed candidate evidence is retained.

## Residual limitations

The five-profile schedule and separated strip construction are structured input
distributions, not exhaustive coverage of all lawful ARC grids. Every ordinary
scene has an active transformation and all teaching motifs; identity-only scenes
are intentionally outside this sampler. Constrained exact overrides can have
weaker teaching coverage. The strict validator defines a canonical envelope,
not equality to the observed examples. The 25% strict-support floor is measured
in the official gate and is not an assertion that every default is strict.

Finite rival tests establish distinctions only against the declared hypotheses.
They do not prove unique induction or Qwen3.5-9B improvement. Python reference
logic in tests/probes is diagnostic; the Racket receipts identify authoritative
comparisons. See the packet's `DECISIONS.md`, `QUESTION_ANSWER.md`, and `checks/`
for sampling denominators, before/intermediate/final evidence, and exact commands.
## Current reviewer considerations

Source SHA-256: `08004f5c2009ed1721b8c2b8727bd277cc49efd32c5956fca1bfd8b0753a57dc`.

# Decisions — review-de3a83533182ed07

Task `249b59452da6`, final version 3.0.1, generator SHA-256
`08004f5c2009ed1721b8c2b8727bd277cc49efd32c5956fca1bfd8b0753a57dc`.
All counts below are tied to retained evidence; diagnostics are not training
approval or measurements of model learning.

## D1 / R1: Preserve the local canonical rule; align the selected authority

The canonical examples and program agree on simultaneous, original-input 2x2
eligibility. A red diagonal needs two zero opposite corners. The baseline
sampler's isolated objects were a distribution restriction, not the rule.
The original rationale for that restriction is unknown; imported notes do not
justify excluding all canonical distractors.

I rejected simplifying the rule to isolated components, filling a component
bounding box, or treating any diagonal color as active. Nine executable rivals
fit all five canonical pairs, so canonical fit alone cannot defend those choices.
The final Racket parity probe compares 758 inputs, including five canonical pairs
and all 729 2x3 grids over {0,2,7}; all agree with the independent diagnostic.
See `checks/contract-final/report.json` and its Racket batch archive.

The bound base JSON selected target was textually divergent. Its
`racket_target.target_code` now exactly matches the unchanged canonical
`program_solution`; `canonicalization_status` records this alignment. Archival
`raw_code` is byte-identical. No canonical row or shared gate was changed.
Authority-sync and rule-smoke pass. This does not claim equivalence on every
arbitrary input beyond the inspected rule and tested domain.

## D2 / R2: Exact controls and explicit bounded support

The baseline advertised controls it did not reliably realize. The retained
7x7/request-five example returns four windows for seeds 0..9, index 0. Evidence:
`checks/baseline-underfill.json`, `checks/before/`, and `checks/red-corrected.log`.
Random placement with a finite retry cap can silently shorten a draw, so I
replaced it with constructive layouts and finite geometry enumeration.

The four controls have pixel-observable meanings: height/width 4..18, eligible
original-input window count 1..10, and distinct input palette size 2..5 including
zero and red. Counts include overlapping windows. All supplied values must be
actual integers; unknown axes, booleans, floats, strings, None, and out-of-range
values fail. The old unused texture and palette-mode knobs are removed instead
of pretending to support them.

Small, two-color, or extreme-count draws use subsets of one checkerboard parity
in a 4x4..4x6 box. Full enumeration is bounded and cached; candidate filtering
uses input geometry only. Required nonred colors are placed outside every
protected completion corner. The final probe covers all 9,000 joint tuples at
seed 0, index 0, default difficulty: 8,985 exact grids and 15 structured refusals.
It also checks 176 one-axis requests and rejects 116 invalid requests. A refusal
is a limitation of this family, not a mathematical impossibility theorem. I
rejected calling arbitrary failed placement attempts impossible or silently
clipping a requested count. Compact overrides have reduced teaching coverage;
the ordinary-curriculum guarantee does not extend to them.

## D3 / R3: Restore canonical scale, palette, and morphology

The baseline produced only red and zero, despite unchanged nonred distractors in
all canonical inputs; it scored 0/60 exact dimension/palette profile hits.
The repair cycles four canonical tuples (10x12/3, 11x11/3, 12x10/4, 9x13/3) and a
broader 9..18, palette-3..5 profile. The schedule is explicit and independently
seeded content remains variable. The final profile floor gets 45/60 exact hits,
with nonzero support in every band, and 48/60 envelope hits. Evidence:
`checks/after-final/checks/249b59452da6_after_profile_floor.json`.

The first candidate over-corrected by putting too many separated objects in every
scene: 12..21 against canonical median 6, failing defect lint while 11 other
stages passed. I retained that failed run under `checks/after/` and introduced a
smaller 2/3-window family. It combines several teaching cases within one T-shaped
red structure and one compact foil. The final defect lint passes without gate
changes. This is marginal support, not a fitted reproduction of canonical grids.

General validation requires lawful rectangular integer ARC colors, dimensions,
active windows, a palette in range, and at least half zero background. Strict
validation adds the canonical dimension/palette envelope, both orientations,
at least two windows, and foreground at most one quarter. All five canonical
inputs pass. A declared strict-support floor of 0.25 leaves room for broad
examples; measured final semantic support is 48/60, and the larger task probe
accepts 81/100 per band. Identity-only and denser scenes are intentionally not
ordinary samples; expanding to them would need an explicit curriculum decision.

## D4 / R4: Put the distinguishing evidence within each ordinary grid

An ordered alternation of easy positives and rare foils can become ambiguous
when lessons start at another index or a query is rotated into demonstrations.
I rejected relying on a lucky first-three-example schedule. Every ordinary input
instead contains both orientations, an overlapping completion, an edge window,
connected red structure, unchanged red bar, and occupied/nonred foils.

Counts two and three use a T motif. Larger counts use a chain and a tailed zigzag,
with optional isolated pairs. The foil also includes a third red corner. Code
review found that allowing that corner and rejecting orthogonal attachments fit
canonical pairs and survived the earlier candidate. Both mistakes now have
explicit rivals and separating inputs. `tests/test_review_motifs.py` provides
independent implementations, anchors, canonical checks, and generated cases;
its baseline and final records are under `checks/new-motif-regressions/`.

The official production sampler has 300 lessons, 1,200 pairs, 1,200 unique inputs,
and 1,200 query rotations with zero ambiguity, hook warnings, or scoring errors.
It uses per-task/band/index hash-derived seeds and consecutive start indices
0..99 in each of easy/medium/hard. Its reporting modulus 6 is not the generator's
five-profile period. The task probe additionally enumerates all 97 consecutive
four-input windows of each seed-0 sequence of length 100 across None/easy/medium/
hard: 1,552 rotations from 400 original inputs. Every canonical-fitting rival
has three distinct refuting demonstrations in each tested rotation; the requested
floor was two. Racket-backed census evidence and Python diagnostic rotations
are distinct populations and must not be added into a unique-input total.

Every ordinary grid sharing this rich motif vocabulary is itself a support
restriction. The review found and repaired two concrete additional shortcuts;
unknown shortcuts remain possible. Twelve rivals are not an exhaustive space of
rules. See `checks/code-review-final/REVIEW.md` for independent final review.

## D5 / R5: Build reusable diagnostics without changing shared policy

The new task-local `workspace/contract_probe.py` reads declared registries,
records failures and source hashes, supports exhaustive joint controls and tiny
Racket cases, and checks distinct teaching support even when a rival also agrees
on the query. Full grids are gzip-compressed with hashes, sizes, record counts,
and restoration instructions. An integrity-error regression ensures a failed
artifact check still produces a truthful report after streams close.

I rejected using Python mirrors as training label authority and did not modify
shared acceptance/export tools. F1 in `FEEDBACK_TO_CODEX.md` proposes an opt-in
shared teaching-support gate; `QUESTION_ANSWER.md` states its false-positive
tradeoff and cheap test. No model training was performed.

## D6: Keep execution problems and solve exposure honest

The initial root suite had three task-tooling failures because its child Python
sets PYTHONNOUSERSITE=1 while pytest was installed only in the user site. The same
three failures reproduce on the original ZIP. A private venv with pytest and
system dependencies fixes them; the complete suite then has 359 passes and
three optional torch skips. No shared source fix was necessary. The environment
bootstrap and failed/passing logs remain in `checks/repository-tooling-diagnosis/`.

The required blind task was completed before inspecting the repair target.
The later solve declares prior exposure yes, reads visible challenge data only
during the episode, and retains one genuine successful visible revision. Both
hidden scores remain unknown. Neither log is claimed to be a token-level model
trace, an unexposed second solve, or evidence of training improvement.

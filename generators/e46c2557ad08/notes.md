# Working notes: e46c2557ad08

## Current accepted parametric family

`workspace/parametric/` exposes three episode-fixed choices under the existing
`preprocess` key: `none` is the exact canonical program; `blue_to_gray` merges
blue into gray, recomputes components and selects horizontal dominoes;
`nearest_vertical` selects the uniquely nearest horizontal domino to the vertical
anchor using Manhattan distance. All three original Racket program texts are
preserved; the first two keep their prior names and meaning.

The merge uses separate rule choices, not an invented Cartesian composition.
Its matched sampler supports 2–6 demonstrations and 1–4 queries, normally 3/4,
with a substantive 30×30 query. The auxiliary `scene` helper now requires at
least 12×15 to accommodate the common teaching geometry; native adapter count
limits and `program`/`generate` interfaces remain unchanged.

Astra found an actual two-demo metric/position ambiguity in the first merge.
The repaired first teaching scene rejects the named distance and coordinate
shortcuts without adding demonstrations. All nine retained parametric test
methods (39 subtests) and five new methods passed; the bounded protected audit
ran 528 evaluations. Owner qualification and fresh acceptance each replayed
all three settings at seeds 0/17; both causal witnesses also passed protected
owner execution. These are finite grammar/seed/rival checks.

Current authority is `parametric/accepted.json`. Portable reconciliation,
resolved counterexample, source diff and proof are under
`evidence/owner-parametric-reconciliation/manifest.json`. The original two
reviews remain source-bound provenance, not approval of later bytes. Ordinary
production source and canonical authority are unchanged; pre-existing canonical
audits and training admission remain separate.

## Current decision

Version `2.0.0`, final reviewed generator SHA-256
`b63464a0ca49196e4166345f842ace658b6e90ae32e31488d77fd9ae5ae5cb16`.
The pinned canonical rule hash is `bba257d19e2b`; the Racket authority was not changed.

The supported ordinary input domain is intentionally all-gray foreground (5) on black (0).
Recolor exactly 4-connected 1×2 horizontal gray components cyan (8). A vertical domino and
one horizontally-adjacent non-domino (`h3`, `h4`, or 2×2 square) are mandatory negative
examples. All components have a one-cell halo.

Public exact axes:

- `grid_h`: 8..14
- `grid_w`: 9..16
- `domino_count`: 1..6

Unknown, retired, lossy or out-of-range overrides are rejected. Constructive lattice
placement guarantees every documented integer combination without retries.

## Lesson contract

Two demonstrations are required. Named rivals are `all_gray_dominoes` and
`any_horizontal_pair`; mandatory witnesses are `vertical_domino` and
`horizontal_pair_near_miss`. The final 300-lesson census checked 900 query rotations with
zero ambiguity against these declared competitors.

## Reversed prior choices

The imported version advertised broad palette/texture/density/position controls and grid
ranges down to 5, but several controls were dead or diagnostic aliases and many valid
metadata values were rejected by band-specific draws. Those controls were removed and the
integer ranges narrowed to the fully constructive domain. The baseline evidence is
`checks/before/checks/e46c2557ad08_before_battery_summary.json`; final evidence is
`checks/after/checks/e46c2557ad08_after_battery_summary.json`.

## Known limit

Because ordinary inputs are all-gray, a color-blind extension that recolors every exact
horizontal domino regardless of color is indistinguishable in-domain. An exact blue-domino
counterexample and canonical Racket output are retained at
`checks/question/e46c2557ad08/evidence.json`; the generator deliberately does not emit
that out-of-domain case.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b63464a0ca49196e4166345f842ace658b6e90ae32e31488d77fd9ae5ae5cb16`.

# Decisions for e46c2557ad08

## D1 — Preserve the all-gray domain instead of expanding color semantics

The canonical task recolors exact horizontal gray dominoes. The imported generator and
all canonical demonstrations use black background plus gray foreground. I retained that
promise explicitly (`self_check` accepts only colors 0 and 5) rather than inventing a
broader color distribution whose outputs would require additional rule interpretation.
The cost is documented: a color-blind horizontal-domino extension is answer-equivalent
on the supported domain. See `QUESTION_ANSWER.md` and
`checks/question/e46c2557ad08/evidence.json`.

Rejected alternative: emit arbitrary colored dominoes. That would disambiguate the
cross-color extension, but it would also broaden the training domain beyond the generator's
established promise and make the gray-specific rule depend on examples absent from the
canonical set.

## D2 — Remove decorative axes and make the remaining axes exact

The previous surface advertised palette, density, position and texture controls that were
ignored, overlapped negative fixtures, or bypassed ordinary construction. I removed them
from `AXES` and retained only values directly recoverable from returned pixels:
`grid_h`, `grid_w`, and `domino_count`.

The prior choice was a broad nominal surface. The new choice is a smaller falsifiable
contract. Evidence: baseline override failures in
`checks/before/checks/e46c2557ad08_before_battery_summary.json`; final override status
`PASS` in `checks/after/checks/e46c2557ad08_after_battery_summary.json`.

## D3 — Narrow dimensions to the domain that is constructively guaranteed

The old metadata claimed heights and widths down to 5 while also requiring multiple
separated objects. I chose height 8..14 and width 9..16 because every combination with
1..6 target dominoes can be built with the two mandatory distractors and a one-cell halo.
The focused test exhausts all 7 × 8 × 6 = 336 integer combinations.

Rejected alternative: keep 5..14 / 5..16 and declare many incompatibilities. That would
make the public contract harder to use and preserve values that cannot teach the full rule.

## D4 — Use constructive placement rather than bounded random retries

Targets are selected from one of several three-cell-spaced lattices after reserving the
mandatory distractor halos. This gives a proof-like feasibility path for every advertised
combination and avoids silent underfilling after a retry budget. Randomness remains in the
lattice choice, slot order and global flips.

## D5 — Put both structural counterexamples in every ordinary scene

A vertical domino refutes “recolor every gray two-cell component.” A horizontal triomino,
horizontal tetromino or 2×2 square refutes “recolor every component containing a
horizontal adjacent pair.” These are declared as witnesses and named rivals, and every
ordinary generated grid carries both.

Rejected alternative: make distractors optional and rely on aggregate frequency. That can
produce individually ambiguous lessons even if a large census eventually observes a
counterexample.

## D6 — Use two demonstrations and require arbitrary query rotations

`EXAMPLES_NEEDED = 2`; `lesson_identifiable` validates all pairs and rejects declared
rivals that fit demonstrations but change the query. The final required-rotation gate
checked 36/36 rotations, and the larger census checked 900/900 rotations with no ambiguity.
This is stronger than relying only on the production order.

## D7 — Leave the Racket authority unchanged

The repair concerns generation and executable contracts, not the canonical transform.
`RULE_HASH` pins `bba257d19e2b`; `racket_lint` and `authority_sync` are green. No reference
rule or canonical data was edited.

## D8 — Keep failed and interrupted evidence

The 36-failure TDD run is retained in `checks/process/tdd-red.log`. The final battery's
outer invocations were interrupted between receipt-backed stages, so the successful run
used `--resume`; all interruption and final logs remain under `checks/process/`. No green
result was inferred from an incomplete parent process.

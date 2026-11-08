# Working notes: 6a289c5b0897

## Accepted interpretation

The executable selected authority, not the prose phrase “unique shortest path,”
is decisive. It chooses the row-major first terminal and performs BFS with
neighbor order Up, Down, Left, Right. The four canonical pairs all admit the
plausible Left, Down, Right, Up rival, so tie order must be taught explicitly.
The selected Racket authority was not edited.

## Review repair (candidate 4.0.1)

Baseline `3.0.0` had no `RULE_HASH`, did not implement the full advertised exact
override domain, accepted unknown controls, and had no executable semantic rival
contract. The replacement constructively realizes every feasible axis tuple,
raises structured incompatibility only for impossible dimension/path requests,
pins `RULE_HASH=d0e77b114425`, supplies strict validation and a Python rule mirror,
and exposes the left-first BFS rival.

Three deterministic profiles cover canonical scale, broad geometry, and an
explicit tie-order witness. The first large rotate-query census found that one
witness per three demonstrations was insufficient: 42/1,200 rotations removed
the only counterexample. Version `4.0.1` retains the three-profile schedule and
adds an independent parity-staggered witness, yielding at least two witnesses in
every four consecutive pairs. The rerun found 0/1,200 ambiguous rotations.

## Reusable evidence

`workspace/qualification_probe.py` verifies canonical shortcut fit, cyclic lesson
starts, every leave-one-out rotation, source hashes, and one exact generated
counterexample. Final probe: 216/216 cycles and 864/864 rotations passed. Final
battery: 12/12 green; focused task tests: 20/20; 300-lesson census: 0 ambiguity.

## Limits

The semantic check is finite and names one strongest plausible rival; it does not
prove universal induction against every imaginable program. Four of every six
scheduled draws deliberately use the tie-witness geometry, so the final domain is
biased toward two-axis down/left branch cases while retaining ordinary geometry
on the remaining draws. Approval remains a catalog decision outside this review.
## Current reviewer considerations

Source SHA-256: `7ac5a6e189f84bece2eb0ebda1efdd0e353833d165ffdeb2afb3dda06fc367fe`.

# Decisions for `6a289c5b0897`

## D1 — Treat the executable authority as normative

**Evidence.** The prose description says “unique shortest path,” but the canonical
pairs have multiple shortest routes. The selected Racket program deterministically
uses the row-major first terminal and Up, Down, Left, Right neighbor order. A
Left, Down, Right, Up BFS reproduces all 4/4 canonical outputs, proving the
canonical demonstrations alone do not identify the tie order.

**Decision.** Preserve the selected Racket authority and pin its normalized hash
`d0e77b114425`; encode the exact order in the generator contract and tests.

**Rejected alternative.** Enforcing unique shortest paths would make tie order
irrelevant and would follow the prose, but it would narrow away an executable
semantic distinction present in the authority. Rewriting the authority to “any
shortest path” was also rejected because outputs must remain deterministic and no
canonical evidence justified a rule change.

## D2 — Replace rejection-heavy layout sampling with constructive geometry

**Original rationale.** Baseline `3.0.0` randomly placed walls, then searched for a
long enough reachable endpoint pair. That was simple but could not honor all
advertised joint overrides and needed a fallback that ignored requested shape.

**Decision.** Choose dimensions and exact Manhattan path length first, construct a
protected lawful route, then place the requested number of walls outside it. This
makes valid generation deterministic and makes failures attributable to genuinely
impossible dimension/path combinations.

**Failure modes checked.** Maximum distance, wall capacity, endpoint count,
reachability, deterministic replay, output purity, global Python RNG isolation,
and exact observation of each axis.

## D3 — Make exact controls fail closed

All five `AXES` controls are validated before generation. Unknown controls,
non-integral dimensions/path lengths, invalid endpoint colors, and out-of-range
densities raise. Feasible joint overrides are exact. Requests such as `h=4,
w=5,min_path_len=8` are explicitly marked incompatible because their requested
terminal distance exceeds the grid diameter.

**Rejected alternative.** Per-difficulty local domains were not retained for exact
overrides; they contradicted the public global domain and caused the baseline
checker’s 570 generation errors. Difficulty now shapes defaults, not legality.

## D4 — Name and execute the strongest surviving rival

The strongest plausible shortcut is BFS with neighbor order Left, Down, Right,
Up. It fits every canonical pair but differs on a two-axis tie. I exposed it in
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`, tied it to an
executable witness, and added a source-bound probe rather than relying on prose.

The exact retained counterexample is seed `910000`, sample `0`, easy band; the
Racket answer matches the intended UDLR output and differs from the rival. See
`checks/question/6a289c5b0897/evidence.json`.

## D5 — Preserve profile completeness and add rotation redundancy

The first repair used a three-profile permutation: `canonical_anchor`, `broad`,
`order_witness`. Every three demos covered all profiles and refuted the rival.
The required rotate-query census nevertheless found 42 ambiguous rotations:
holding out the sole `order_witness` sometimes left three rival-compatible demos.

**Decision.** Keep the three-profile schedule, and independently require witness
geometry whenever `(seed + sample_index)` is even. Parity alone supplies exactly
two witness positions in every four consecutive draws; the named profile can add
more. Every three-draw lesson still covers all distribution profiles, while every
leave-one-out rotation retains at least one semantic witness.

**Rejected alternatives.** Increasing `EXAMPLES_NEEDED` would make episodes larger
and still require careful residue analysis. A four-profile sequence with duplicate
witness names would break the useful every-three profile-completeness contract.
Making every sample a tie witness would guarantee teaching but unnecessarily
remove ordinary/straight geometry. Stochastic rejection until a witness appears
would be less transparent and harder to prove over cyclic starts.

## D6 — Build a reusable qualification probe

`workspace/qualification_probe.py` loads declarations from the selected generator,
checks every declared canonical shortcut against canonical pairs, exercises all
requested cyclic starts, rotates each four-pair window through every query
position, records source hashes, and saves an exact counterexample. It is intended
for future reviewers and is covered by the task suite.

Final run parameters were 12 seeds per band and 6 starts: 216 cycles, 864
rotations, 0 failures, 324 unique inputs. The separate production-sampler census
used 100 lessons per band and found 0/1,200 ambiguous rotations.

## D7 — Leave the Racket authority unchanged

Python mirror parity against all canonical pairs, rule smoke, Racket lint, and
authority synchronization passed. Changing Racket would have increased review
risk without fixing the actual input-distribution and teaching defects. The
selected authority remains hash `d0e77b114425`.

## D8 — Audit targets are findings-only

For `94ff484354c0`, I reproduced an exact-control defect: opposite declared
palette kinds and helpful textures yield byte-identical lawful inputs. For
`d546d87fec58`, I generated a fully controlled `mixed_fallback` case that passes
validation, matches Racket, and refutes rotate-180-only; its portable task suite
passed 333/333. Neither audit target was modified, as required.

## Remaining limitations

The declared rival set is not an exhaustive program synthesis proof. The final
distribution deliberately allocates four of six schedule residues to order-witness
geometry, which improves teaching robustness but biases endpoint orientation.
The exact axes remain intentionally small (`h=4..6`, `w=5..8`, path length
`3..10`). Catalog approval and train safety remain outside this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f50a735ac2750349:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7ac5a6e189f84bece2eb0ebda1efdd0e353833d165ffdeb2afb3dda06fc367fe`. At disposition, audited bytes match the current source.

### Current decision

The retained audit explicitly reported no issue in its bounded source-bound scope. Preserve that limitation; no universal correctness or new owner execution is inferred.

### Assessment or prior finding

## 6a289c5b0897

**No issue found.** I checked the assigned generator hash
`7ac5a6e189f84bece2eb0ebda1efdd0e353833d165ffdeb2afb3dda06fc367fe`,
its pinned rule hash, exact-control and validation tests, the canonical-fitting
Left/Down/Right/Up BFS rival, finite schedule residues, query rotations, and
selected-authority synchronization. Fresh portable task tests pass 20/20
(`checks/audit/6a289c5b0897/task-tests/result.json`). The source-bound
qualification probe passes 216/216 cyclic windows and 864/864 leave-one-out
rotations over 324 unique inputs while confirming that the named rival fits all
4 canonical pairs (`checks/audit/6a289c5b0897/qualification-probe.json`). Exact
selected-authority execution parity passes in
`checks/audit/6a289c5b0897/authority-sync/result.json`.

The audit remains finite: it tests the declared strongest rival and the documented
schedule, not every conceivable program. The target was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-f50a735ac2750349-v0001/audit_assets.json), manifest SHA-256 `dd44996cf7fcc2663bf1076af4a67a33f44ce21d6c29173d1c61460d90664ded`.
<!-- arcpuzzles-current-audit-assessment:end -->

# Working notes: ada76e18c19c

## Current native parametric extension (owner acceptance pending)

The separate `workspace/parametric/` family preserves exact canonical row filling
and adds `filled_majority`: fill first, then retain the global winning color,
including its disconnected pieces. It supports 3–6 demonstrations and four
prefix-stable private queries, ending at substantive 30x30. The original narrow
production grammar and approved source are unchanged.

Self-review found first/last/min/max-color teaching shortcuts in independent
random lessons. The repaired three-demo schedule cycles color roles and vertical
order; a source-pinned protected-Racket audit retains the old ambiguities and
new separating demonstrations. Final self-review also exposed a qualifying-row
frequency shortcut; one long winning row versus two shorter losing rows now
refutes it, with executed before/after evidence and no extra demonstrations.
A second regression raised the dense stress-row
floor after seed 8 exposed only 89 nonzero input cells. The final 64-seed sweep
has 512 episodes, 4,352 labeled-pair checks, 640 distinct inputs, 22 policies,
81 protected-Racket evaluations and no failures. Failed development receipts
remain explicitly named. Post-fill ties are tested but not sampled in queries.

Native qualification and the wrong-order causal witness are returned separately;
no owner acceptance or training admission is claimed. See the workspace README
and task-local evidence/current/audit.json for commands, exact cases and limits.


## 2026-09-28 review

The imported `2.0.1` generator expressed the broad idea correctly but did not match the authoritative task distribution or expose a testable semantic contract.

### Baseline findings

- Generated dimensions were `4..6 × 7..9`; all five canonical inputs are `6..9 × 9..12`.
- Exact canonical-profile support was `0/60`; only `7/60` draws entered the broad canonical envelope.
- Eight axes were declared, but several were inert aliases/singletons and the override checker produced 12,192 findings.
- Degenerate textures were mixed into the normal texture domain.
- `self_check` accepted a solid `2×2` block and only required one same-color pair.
- There was no pinned `RULE_HASH`, rule mirror, strict recognizer, rival/witness set, or lesson-identifiability contract.
- Random color selection could repeat colors despite the summary claiming distinct active-row colors.

### Selected design

Keep only two honest exact axes: height and width. Cycle the five canonical `(height, width, palette-size)` profiles on the default path. Always include exactly three valid active rows with distinct colors.

Separately cycle three negative row types. Each type falsifies one canonical-ambiguous rival:

- mismatched endpoints falsify “fill any two nonzero cells”;
- three same-color cells falsify “one repeated color is enough”;
- a third-color blocker falsifies “a color occurring twice is enough.”

Three consecutive demonstrations contain all three witness types. Witness cells are vertically attached to existing endpoint components, preserving the canonical connected-component median of six.

### Verification

Focused regression tests live in `tests/test_generator_ada76e18c19c.py`. The repository after-battery finished with all 12 stages green. Key measured results:

- canonical profiles: `60/60` exact and `60/60` envelope;
- semantic strictness: `600/600` generated draws and `5/5` canonical inputs accepted;
- witnesses: `3/3` firing, all rival claims verified;
- lessons: `12/12` identifiable across easy/medium/hard;
- Racket smoke: `120/120` mirror agreement;
- mutation sensitivity: `54/54` destructive mutations rejected;
- overrides: `2,250/2,250` accepted contract draws, zero findings;
- diversity: `100%` unique inputs and outputs in the 50-episode probe.

### Known limitation

The generator deliberately keeps the authoritative task grammar narrow: three qualifying rows, three nonzero colors, and official default profiles. It does not attempt to teach arbitrary palette sizes, more/fewer active rows, nonblack backgrounds, or endpoint gaps below three because none are needed to identify the selected rule and each would broaden the distribution beyond the canonical evidence.
## Current reviewer considerations

Source SHA-256: `0fc03c3b4e7e07c5390a25d706b4595ae468fc8e4b4c376a1093dbf532044d4f`.

# Decisions: ada76e18c19c

## D1 — Preserve the authoritative Racket rule

**Input choice:** Treat the canonical Racket program and rule hash `714e73d2362f` as authoritative; improve the input curriculum rather than alter the transformation.

**Original rationale:** The imported generator did not record one. The canonical written solution and all five input/output pairs agree with the Racket exact-count/exact-color condition.

**Alternatives considered:** Rewrite or simplify the Racket; broaden it to fill rows with blockers or mismatched endpoints; make the Python generator define the authority.

**Probe:** Canonical replay, 120 generated Racket applications, and 120/120 agreement with the new independent Python mirror.

**Failure mode avoided:** A superficially simpler rule could accidentally teach “two endpoints are enough” while changing authoritative behavior on rows with extra cells.

**Limitation:** The canonical rule’s behavior on malformed non-ARC grids is outside scope.

## D2 — Cycle all five exact canonical profiles

**Input choice:** Default dimensions cycle `(7,10)`, `(8,9)`, `(6,11)`, `(9,12)`, `(8,10)`; every draw has palette size four.

**Original rationale:** Unknown. The old `4..6 × 7..9` bounds appear generic rather than derived from this task.

**Alternatives considered:** A wide random envelope; one canonical anchor mixed with broad random grids; difficulty-specific dimensions.

**Probe:** The strict profile floor measured `60/60` exact matches and at least one match in every band, versus `0/60` before.

**Failure mode avoided:** A model trained only on small grids could infer a size-correlated shortcut and never see the actual public geometry.

**Limitation:** The default dimension frequencies are uniform over a five-step cycle rather than weighted by an external deployment distribution, which is unknown.

## D3 — Retain only observable axes

**Input choice:** Expose only `grid_h` and `grid_w` as exact overrides.

**Original rationale:** The old metadata listed palette aliases, row counts, palette sizes, distinct-color counts, singleton position/density labels, and texture modes, but most had no honest effect or no recoverable observation.

**Alternatives considered:** Implement all eight old axes; mark most diagnostic; keep texture as a mixed helpful/degenerate axis.

**Probe:** The strict override matrix completed 2,250 draws, 25 cases, and three bands with zero findings. The prior matrix produced 12,192 findings.

**Failure mode avoided:** Accepted overrides that silently do nothing, clamp to a band, or return a grid whose realized value cannot be measured.

**Limitation:** Callers cannot directly request a witness type; the witness schedule is intentionally sample-index-driven so lesson coverage remains replayable.

## D4 — Fix the positive grammar at three distinct active rows

**Input choice:** Exactly three qualifying rows use three distinct nonzero colors, each with endpoint distance at least three.

**Original rationale:** The old summary claimed two to three rows and distinct colors, while its random choices did not enforce distinctness. Every canonical input actually has three qualifying rows and three distinct colors.

**Alternatives considered:** Preserve two-to-three variability; expose active-row count as an axis; allow repeated colors.

**Probe:** Direct canonical census, focused tests over 15 scheduled samples in four difficulty settings, and strict semantic census over 600 draws.

**Failure mode avoided:** Palette/profile drift and ambiguous attribution when one color is reused across positive rows.

**Limitation:** The generator does not test whether the transformation generalizes to one, two, or four qualifying rows. That is a deliberate canonical-evidence boundary, not an inferred impossibility.

## D5 — Add one counterexample row on a three-step schedule

**Input choice:** Rotate mismatched pair, three-same-color, and blocked-pair rows. Set `EXAMPLES_NEEDED = 3`.

**Original rationale:** None; the old generator put some negative textures behind overrides but did not schedule them into ordinary lessons or verify their semantic effect.

**Alternatives considered:** Put all three negative rows in every grid; add random negatives; use only one strongest blocker example; leave examples purely positive.

**Probe:** All three shortcuts match all canonical pairs, all three named witnesses fire across every band, each rival claim passed 60/60 checks, and 12/12 materialized lessons were identifiable.

**Failure mode avoided:** A model can otherwise learn a canonical-equivalent shortcut and receive no contradictory training example.

**Limitation:** Lessons shorter than three examples can omit a witness profile.

## D6 — Preserve morphology while adding negative evidence

**Input choice:** Place witness cells adjacent to endpoints of existing positive components, so they merge vertically rather than creating extra connected components.

**Original rationale:** Newly derived during review. A naïve counterexample row raised object count from the canonical median six to eight or nine.

**Alternatives considered:** Ignore morphology; include isolated witness cells; place all witnesses in one dense row.

**Probe:** Distribution gate after the change reports generated medians equal to canonical medians: object count `6.0`, component-size median `1.0`, palette `4.0`, aspect `10.0`, and area `71.0`.

**Failure mode avoided:** Solving the semantic gap by introducing an unrelated morphology cue that distinguishes generated examples from canonical ones.

**Limitation:** Connected-component equivalence is only one distribution marginal; it does not prove complete visual indistinguishability.

## D7 — Make structural acceptance narrow and executable

**Input choice:** `self_check` requires canonical dimensions, exactly three nonzero colors, exactly three distinct qualifying rows, legal gaps, and at most one declared witness row. `strict_canonical_like` additionally requires one of the five exact official profiles.

**Original rationale:** The old check only looked for one qualifying row and accepted a solid `2×2` block.

**Alternatives considered:** Keep a permissive validator; validate only dimensions/palette; special-case degenerate textures through metadata.

**Probe:** Five canonical inputs accepted, 600/600 generated draws accepted, and 54/54 destructive mutations rejected.

**Failure mode avoided:** A generator can appear healthy while its checker blesses task-free or contradictory grids.

**Limitation:** The validator intentionally rejects structurally valid but out-of-curriculum examples such as two active rows.

## D8 — Add reusable semantic/test tooling in the task home

**Input choice:** Add `rule_mirror`, `semantic_profile`, named rivals/witnesses, lesson checking, mutation fixtures, and seven focused tests.

**Original rationale:** No prior executable semantic contract existed.

**Alternatives considered:** Document the intended cases only; rely exclusively on the global battery; add an external one-off analysis script.

**Probe:** The focused test was first observed failing on missing hooks, then passed `7/7`; all repository battery stages passed.

**Failure mode avoided:** Future agents changing layout code without realizing they removed the only counterexample to a canonical-ambiguous shortcut.

**Limitation:** The named rivals are a strong finite set, not a proof that no conceivable alternative program fits a lesson.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ada76e18c19c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

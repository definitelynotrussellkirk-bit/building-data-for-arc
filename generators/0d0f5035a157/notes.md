# Working notes: 0d0f5035a157

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d62c497f5d9bd691389552dd6d5313d0bbab513f63fd19ce975a146cdd93f6de`.

# Decisions for `0d0f5035a157`

## D1 — Replace the baseline texture knobs with six observable axes

**Baseline choice and rationale:** `position_bias` and `density` existed, but no retained rationale was available. Inspection showed they overlapped with hard-coded placement behavior and were not independently recoverable from pixels.

**Decision:** expose `grid_h`, `grid_w`, `palette_size`, `max_cells_per_row`, `n_empty_rows`, and `n_packed_rows`. Each is integer-valued, exact, and recoverable through `observe_overrides()`.

**Alternatives considered:** keep the old names and reinterpret them; add several qualitative placement modes; expose row-by-row layouts. Reinterpretation would preserve misleading contracts, qualitative modes would be hard to lint for exactness, and row-level controls would overfit the implementation rather than the task concept.

**Probe/failure mode:** exhaustive declared boundary combinations and malformed overrides are covered in `tests/test_generator.py`; 12 legal joint cases are replayed by `workspace/review_probe.py`. Unknown keys fail closed rather than being ignored.

**Limit:** exact axes describe aggregate morphology, not every possible row arrangement.

## D2 — Canonical-linked dimensions and palettes without canonical cloning

**Baseline choice and rationale:** the v2 description broadly targeted similar sizes and colors, but the source had no documented weighting rationale.

**Decision:** use 5..10 rows, 8..14 columns, and 1..9 nonzero colors, heavily weighting the four canonical `(height, width, palette)` profiles while still sampling a wider lawful envelope.

**Alternatives considered:** sample only exact canonical profiles; sample all dimensions uniformly. Canonical-only sampling would teach incidental shapes; uniform sampling missed the profile-floor gate too often and diluted direct support.

**Probe/failure mode:** the final profile-floor stage is green, and `review_probe.py` checks canonical-shortcut claims against the actual portable canonical pairs.

**Limit:** weighting is heuristic curriculum design, not an estimate of the hidden evaluation distribution.

## D3 — Mixed row roles

**Baseline choice and rationale:** all active rows were forced to require movement, apparently to avoid identity outputs. That also taught the shortcut “every nonempty row must change.”

**Decision:** allow exactly 0..2 empty rows and 0..2 already-packed nonempty rows; all other active rows require compaction. Keep the maximum-count row moved so every generated grid remains nontrivial.

**Alternatives considered:** permit arbitrary packed-row counts; continue forbidding packed rows; construct a separate unchanged control panel. Arbitrary counts could dominate small grids, forbidding them preserves the shortcut, and a separate panel adds structure unrelated to the row-local law.

**Probe/failure mode:** `self_check()` rejects all-packed and too-few-active-row cases; tests mutate role counts; the solve episode successfully inferred unchanged packed rows as part of one row-wise rule.

**Limit:** at most two packed rows is a curriculum cap, not part of the canonical transformation law.

## D4 — Internal and leading gaps

**Decision:** the designated maximum row always starts at column 0 but contains an internal gap; other moved rows alternate stochastically between internal-gap and leading-gap placement.

**Rationale:** this separates “remove zeros stably” from “shift a suffix left” and prevents column-0 absence from becoming an accidental marker for rows that change.

**Alternatives considered:** purely uniform scatter; leading gaps only. Uniform scatter does not guarantee the critical internal-gap witness; leading gaps only admits a simple prefix-shift interpretation.

**Probe/failure mode:** tests require the designated dense row to be moved and verify stable order. The workspace probe tests every cyclic lesson start and query rotation.

**Limit:** placements remain sparse and row-local; they do not explore adversarial full-width rows because `max_cells_per_row <= 7`.

## D5 — Alternating sparse/dense curriculum

**Decision:** `sample_index % 2` alternates a 3..4-cell sparse role with a 5..7-cell dense role.

**Rationale:** all five usable canonical examples have at most four nonzero cells in any row, so a plausible rival compacts only rows of size at most four. Frequency alone is insufficient: the witness must remain in demonstrations when any pair becomes the query. Alternation gives two dense pairs in every four-pair window.

**Alternatives considered:** random dense frequency; one dense example every four; make every example dense. Random frequency has unbounded witness-free windows, one-per-four can place the sole witness in the query, and all-dense lessons lose canonical-profile support.

**Probe/failure mode:** `review_probe.py` checks 128 cyclic windows and all 512 rotations; `lesson-census` checks 300 production lessons and 1,200 rotations. No declared-rival ambiguity survived.

**Limit:** the schedule refutes the named `pack_at_most_four` rival, not all conceivable data-dependent rivals.

## D6 — Exact palette realization

**Decision:** start each active row with one value, assign `max_cells_per_row` values to the designated row, then distribute additional cells until every requested palette color can appear; shuffle one copy of every palette color through the stream before sampling repeats.

**Rationale:** an advertised `palette_size` must be visible exactly, including at boundary combinations.

**Alternatives considered:** draw colors independently and merely hope all appear; retry until coverage. Independent draws violate exact overrides; retries make support opaque and can bias layouts.

**Probe/failure mode:** boundary tests verify exact palette recovery and deterministic outputs.

**Limit:** palette colors are uniformly selected from 1..9; no semantic role is attached to color identity.

## D7 — Strict self-check and independent Python mirror

**Decision:** validate rectangular ARC cells, dimensions, palette, active/empty/packed role bounds, max-row size, and the existence of a multi-cell moved row. Keep `rule_mirror()` separate from generation.

**Rationale:** the baseline self-check accepted a singleton impostor and therefore could not certify useful teaching morphology.

**Alternatives considered:** validate only the output law; validate exact implementation internals. Output-only checks miss weak inputs, while implementation-internal checks are brittle and circular.

**Probe/failure mode:** mutation tests target each structural condition, and the Racket rule-smoke stage compares the independent authority.

**Limit:** self-check establishes grammar membership, not pedagogical uniqueness.

## D8 — Racket authority synchronization

**Decision:** replace only `racket_target.target_code` in the selected base-solution JSON with the canonical stable row-compaction expression. Preserve `raw_code` exactly.

**Rationale:** the before authority-sync stage found textual divergence even though execution agreed. Normalizing the active source removes ambiguity while preserving the archival record.

**Alternative:** leave the behaviorally equivalent text untouched. Rejected because the selected authority contract explicitly requires synchronization.

**Probe/failure mode:** final rule smoke, Racket lint, and authority sync are green. `raw_code` SHA remained `144d7659…`.

## D9 — Reusable source-bound probe

**Decision:** add `workspace/review_probe.py`, which imports the current generator, dynamically reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies those shortcuts really fit every usable canonical pair, enumerates all cyclic lesson starts/query rotations, and exercises joint override boundaries.

**Rationale:** copied rival lists and one-off seed checks go stale as source changes.

**Alternative:** rely only on the shared census. Rejected because the production census does not enumerate every deterministic schedule start and its finite sample cannot prove exact joint-axis support.

**Limit:** the tool intentionally evaluates declared competitors. Undeclared rivals still require human adversarial review.

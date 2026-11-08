# Working notes: d5af7195f6da

Review `review-84e5a0c969f36ade` replaced the version-3 random motif sampler. The baseline is retained in `workspace/baseline_generator_v3.py`.

Key evidence:

- Before battery: 4 blockers (`lint`, `defect_lint`, `dist_gate`, `override`).
- Initial rotation census: 676/1,500 ambiguous rotations with one witness per profile.
- Intermediate census: 5/2,400 ambiguous rotations after repeated profiles collided under exact-input de-duplication.
- Final source: 12/12 battery stages, 169/169 portable tests, and 0/2,400 ambiguous rotations over 300 lessons.

The Racket authority was not changed. The Python mirror is validation-only. Domain limitation: fixed height/frame and four constructive topologies prioritize teaching signal over broad free-form diversity.
## Current reviewer considerations

Source SHA-256: `897916ea4e2e6b7812581ff0fd621b80e05694a4eda5606b96ed439049c9b34c`.

# Decisions: d5af7195f6da

## D1 — Replace motifs with singleton seed cells

**Original state:** version 3.0.0 generated 3–5-cell connected motifs. The retained comments called them seeds, but the Racket rule reads every nonzero/non-5 cell as an independent seed cell. The original rationale beyond those comments is unknown.

**Decision:** emit exactly 2–4 singleton seed cells. This matches the canonical representation and makes the same-color seed-cell tie distinction testable.

**Rejected alternative:** retain motifs and merely improve wall placement. That would continue teaching an unsupported object abstraction and make per-cell versus per-object distance shortcuts hard to diagnose.

**Probe/failure mode:** task tests assert every generated colored seed is 4-neighbor singleton. The independent oracle treats cells, not components, as seeds.

## D2 — Use canonical-scale dimensions and a complete wall frame

**Decision:** fix height at canonical 7 and expose exact width 9–11. Every grid has a color-5 frame; profile builders may add interior barriers.

**Reason:** the before profile-floor evidence showed poor canonical support. A complete frame makes the wall role visible in every example and avoids accidental open-boundary interpretations.

**Rejected alternative:** keep 7–20 variable dimensions and random optional walls. It adds surface diversity but no guaranteed semantic evidence.

**Limitation:** this narrows geometric diversity and may let a model associate the rule with framed 7-row arenas. A future expansion should add validated height/topology families only after preserving all four witnesses.

## D3 — Construct four semantic profiles

**Decision:** schedule `distinct_tie`, `wall_detour`, `seedless_chamber`, and `same_color_tie`.

**Reason:** each profile refutes a concrete plausible rival that fits some or all canonical examples. The profiles are independently observable from pixels and work for every legal width/seed-count product.

**Alternatives considered:**

- Pure random barriers: rejected because witness frequency is not lesson coverage.
- One giant scene containing every distinction: rejected because it couples failure modes and reduces test isolation.
- Three profiles without same-color ties: rejected because a solver could treat seed-cell ties as blank even when the tied cells share one color.

**Probe:** `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and task tests require every profile to fire its named witness for all 9 width/count products.

## D4 — Expose only exact, recoverable axes

**Decision:** public axes are `grid_w`, `n_seed_cells`, and `profile`; no incompatibility table is needed because all 36 axis products are legal in each of four difficulty values.

**Reason:** the baseline's palette, texture, density, and position controls were dead, aliases, or not recoverable. Exact controls are more valuable than a broad misleading schema.

**Probe:** task tests enumerate 144 difficulty × joint-axis requests, compare `observe_overrides` with the request, validate the grid, and compare the mirror with an independent oracle. Unknown and malformed overrides must raise.

## D5 — Seven demonstrations plus one query

**Initial attempt:** four demonstrations plus one query covered all profiles in ordered lessons, but `checks/lesson-census-initial-reproducer.json` found 676 ambiguous rotations among 1,500 held-out pairs.

**Decision:** use seven demonstrations and one query, yielding two occurrences of every period-four profile in each eight-pair lesson. Holding out any one pair leaves at least one witness of every profile.

**Rejected alternative:** declare ordered-query-only semantics. Downstream assembly permits rotations, and the assignment explicitly asked for rotation evidence when supported.

**Cost:** lessons are longer. The extra four demonstrations are justified by the measured ambiguity reduction and the small grids.

## D6 — Rotate palettes by profile occurrence

**Intermediate failure:** after moving to seven demos, `checks/lesson-census-v2-reproducer.json` still found 5 ambiguous rotations among 2,400. Root cause was production exact-input de-duplication: repeated profiles could be byte-identical, deleting the spare witness.

**Decision:** deterministically rotate the seed-color palette by occurrence number within the period-four schedule. Semantic roles do not depend on numeric color rank, and same-color tie profiles still repeat the first selected color as required.

**Rejected alternatives:** disable de-duplication, add random retry noise, or increase demonstrations again. Those either change shared assembly, obscure reproducibility, or add token cost without addressing the collision source.

**Probe:** 100 lessons per band assert all first eight production draws are unique and contain exactly two of each profile. The Racket-backed final census confirms no materializer rejection or rotated ambiguity.

## D7 — Keep the canonical Racket authority unchanged

**Decision:** do not modify the selected rule source. Pin `RULE_HASH = ca2bc3cf692f`; use the Python mirror only for validation and local rival probes.

**Reason:** canonical outputs and rule smoke already agreed. The defect was distribution/curriculum, not authority semantics.

**Probe:** final `rule_smoke`, `racket_lint`, and `authority_sync` are green; canonical pairs match an independent BFS oracle and the mirror.

## D8 — Add portable tests and a fast future-agent probe

**Decision:** add `tests/test_review_contract.py` and `workspace/probe_curriculum.py`.

The test file uses a separate BFS implementation, canonical helpers, full joint-axis enumeration, cyclic starts, rotation holdouts, malformed inputs, global-RNG checks, and a source-bound test of the workspace probe. The probe reads the generator's live profiles/rivals, models exact-input de-duplication with consecutive retries, and emits a compact JSON report. It is intentionally mirror-based and therefore cannot replace the Racket census.

## Final self-review

A possible new shortcut is “always expect a rectangular color-5 frame and one of four templates.” That shortcut would fit this deliberately targeted curriculum but not the canonical rule's full lawful domain. I did not claim universal coverage: the repair is accepted as a high-signal training distribution, with the fixed-height/template restriction explicitly retained for a future diversity round.

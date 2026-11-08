# Working notes: e42b0a4cc753

## Review repair

Baseline generator SHA-256: `be5f5d26244be9dfe7c7dddf0ffc8ca0113dbcbcc3779cef186e1caa7f998e37`.
Final generator SHA-256: `e2271d4ce81f37366d64781ce5f29f087e748e3211cd869f1e67181c5d7bb44b`.
Selected rule hash: `f23844d6433c` (unchanged).

The baseline lacked a rule pin and task-specific validator, advertised dead textures and mismatched controls, and supplied no executable teaching contract. More importantly, all three canonical pairs were solved by both a lower-color tie-break and an “ignore seeds after the first two” shortcut.

Version 4.0.0 exposes only exact dimensions and seed count, validates the framed Manhattan-Voronoi grammar, requires every seed to own a blank, and uses a three-role period equal to the lesson demonstration count. The roles guarantee evidence for reading-order ties, third-seed relevance, and Manhattan rather than Euclidean distance.

## Evidence

- Baseline battery: `checks/before/` in the review return.
- Final battery: `checks/after/`.
- Focused portable tests: `checks/task-tests/`.
- 300-lesson source-bound census: `checks/lesson-census.json`.
- Exact canonical-fitting shortcut witness: `checks/shortcut-witness/witness.json`.
- Independent probe: `workspace/voronoi_probe.py`.

## Known limits

The ordinary schedule correlates role with one of three canonical-scale profiles. Exact overrides cover the full dimension/seed envelope, but overridden examples are not promised to carry a teaching witness. Declared-rival census results are finite evidence, not a universal uniqueness proof.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e2271d4ce81f37366d64781ce5f29f087e748e3211cd869f1e67181c5d7bb44b`.

# Decisions for `e42b0a4cc753`

## D1 — preserve and pin the selected authority (R1)

The selected canonical Racket rule was already behaviorally correct, so I did not change canonical or base rule data. I pinned `RULE_HASH = "f23844d6433c"`, added an independent Python mirror for audits, and required exact mirror parity in tests and rule smoke. This avoids converting a generator-quality repair into an authority rewrite.

Rejected alternative: copying or editing the divergent archival base rule merely to make source groups byte-identical. The selected authority had execution parity, and changing an unselected archival record would expand scope without improving generated labels.

## D2 — expose only controls observable in pixels (R3)

The public axes are:

- `grid_h`: integer 6..10;
- `grid_w`: integer 7..12;
- `n_seeds`: integer 2..5.

`observe_overrides` reconstructs all three from the grid. Unknown, mistyped, and out-of-range values are rejected before drawing. I removed the stale texture, palette, variant, and differently named seed-count controls because they were inert, internally inconsistent, or not recoverable.

Rejected alternative: retain old controls as “diagnostic” metadata. These were presented as generation controls and appeared in the override matrix, so relabeling them would conceal rather than repair the contract defect.

## D3 — define a broad but structurally meaningful lawful domain (R1/R3)

The grid has a complete outer border of color 8, a zero interior except for 2..5 singleton seeds, pairwise-distinct seed colors drawn from ARC colors excluding 0 and 8, and at least one blank cell. Every seed must uniquely own at least one blank under Manhattan distance. Dimensions 6..10 by 7..12 preserve the canonical scale while allowing moderate variation.

The ownership condition prevents decorative or causally irrelevant seeds. It also makes the three-seed lesson a constructive witness against ignoring later seeds rather than relying on a seed whose Voronoi region happens to be empty.

Rejected alternatives:

- Permit dominated seeds: lawful labels would remain computable, but seed-count evidence could be semantically inert.
- Permit one/no seed or a broken frame as ordinary “degenerate textures”: those are negative fixtures, not members of the selected rule’s normal task domain.
- Inflate the size envelope: larger grids add area without teaching a new transformation and drift farther from the three canonical profiles.

## D4 — use a three-slot curriculum instead of random witness hope (R2)

The schedule is:

| Slot | Dimensions | Seeds | Role |
|---|---:|---:|---|
| 0 | 6×7 | 2 | reading-order tie counterexample |
| 1 | 6×8 | 3 | consequential third seed |
| 2 | 7×9 | 2 | Manhattan-versus-Euclidean counterexample |

The period equals `EXAMPLES_NEEDED`, so any consecutive three demonstrations include all roles. Layouts are sampled from all geometries satisfying the role predicate, preserving substantial within-role diversity. Difficulty changes the deterministic random stream but not the lesson contract, because weakening a role in an “easy” band would reintroduce ambiguity.

Rejected alternatives:

- Fully random generation plus post-hoc semantic checks: a good aggregate witness rate does not guarantee each assembled lesson contains the needed evidence.
- Resample until all three rivals are refuted in every individual grid: unnecessarily restrictive; each demonstration should carry one clear burden, and the lesson collectively identifies the rule.
- Increase `EXAMPLES_NEEDED`: three examples are sufficient when each has a deliberately different pedagogical role and match the existing solve configuration.

## D5 — distinguish normal pedagogy from exact overrides (R3)

Any explicit override disables the role-specific geometry and uses a broad lawful-layout sampler. This keeps the override promise exact for arbitrary supported combinations. It would be misleading to claim, for example, that a caller-forced two-seed geometry always demonstrates the third-seed rule.

The default schedule covers canonical profiles; override tests cover the full declared boundaries and representative joint combinations. No incompatibilities are declared because every advertised combination is constructively supported.

## D6 — declare executable rivals and witnesses (R2)

Canonical-fitting shortcuts:

- `lower_color_tie`: Manhattan distance, but ties choose the lower seed color;
- `ignore_after_first_two`: use only the first two row-major seeds.

Additional plausible competitor:

- `euclidean_distance`: squared Euclidean distance with the intended row-major tie-break.

The generator exposes these through `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, plus witness predicates and `lesson_identifiable`. The source-bound census found no declared ambiguity in 300 lessons, but this remains a finite hypothesis class and not a universal program-identification proof.

## D7 — keep an independent reusable probe and focused tests (R4)

`workspace/voronoi_probe.py` deliberately does not import `generator.py`. It supports future reviewers who need to test new distance metrics, tie rules, ownership, or disagreement cells without trusting the production implementation. `tests/test_generator_e42b0a4cc753.py` covers authority parity, canonical validation, exact axes, invalid overrides, canonical shortcut fit, role consequences, and every cyclic three-demo schedule window.

The failed TDD stages are retained under `checks/tdd-red-*`; their corresponding passing stages are under `checks/tdd-green-*`. Final portable task-test evidence is under `checks/task-tests/`.

## Remaining limitations

The default sampler intentionally uses only three dimension/seed-count profiles, so role and default shape are correlated. Full-envelope exact overrides demonstrate mechanical support, but downstream training that wants both guaranteed pedagogy and independently randomized dimensions would need a larger constructive role bank.

The lesson census reports the same callable under multiple declaration namespaces; this does not change its verdict but duplicates evidence. A shared-tool improvement is proposed as F2 in `FEEDBACK_TO_CODEX.md`.

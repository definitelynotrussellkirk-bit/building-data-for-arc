# Working notes: e1fc836c1922

Reviewed under assignment `review-dd59f6a68848623a`.

- Baseline source `3d9b08c…` advertised dead/redundant controls, rejected canonical 3-mark inputs, lacked a rule pin, and had no semantic contract.
- Final source `c204f990…` exposes only exact `grid_size`, `n_marks`, and `n_colors` controls; every cross-product is constructive in every band.
- Canonical rule hash `c0c41dfe5b49` was pinned and the Racket authority was not changed.
- The canonical-fitting `upper_triangle_only` rival is refuted by every ordinary draw through a forced lower-triangle source.
- An intermediate battery found a generic short-line validator gap; final placement spans at least two rows and columns.
- Final evidence: 12/12 battery stages green, 40/40 task tests green, and 0/1,200 ambiguous rotated lessons against the declared rival.

See packet-root `REVIEW.md`, `DECISIONS.md`, and `checks/` for commands and retained failures.
## Current reviewer considerations

Source SHA-256: `c204f990d6b222f3feddc9918fe7f9d858c2dee2bba19698bc3d856331f1df66`.

# Decisions for `e1fc836c1922`

## Evidence intake

The selected baseline was SHA-256 `3d9b08c4eaab4b968bb6e11f85d06ada9240e11189e077ce12098ac925c23f13`. I used prior return `review-bd13faec85d141fd:v0001` only as a lead. Its claims were remeasured against the pinned packet baseline; the before battery reproduced the missing rule pin, dead textures/axes, canonical rejection, and override failures.

The original rationale for most baseline axes is unknown. The baseline comments described sparse colored marks and an additive main-diagonal reflection, but no evidence justified separate `grid_h`, `grid_w`, palette aliases, corner flags, or negative textures as ordinary exact controls.

## D1 — Keep the canonical rule unchanged

**Choice.** Leave the selected Racket authority unchanged and pin `RULE_HASH = "c0c41dfe5b49"`.

**Rationale.** Rule smoke and authority sync passed before repair. The failures were generator, validator, metadata, and teaching-distribution defects—not a wrong transformation.

**Alternative rejected.** Rewriting/beautifying the Racket rule would add authority risk without fixing any reproduced defect.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green; `checks/shortcut/racket.json` executes the same hash.

## D2 — Replace fictional controls with three honest exact axes

**Choice.** Expose only `grid_size=5..12`, `n_marks=3..9`, and `n_colors=1..3`.

**Rationale.** These are observable properties that genuinely change the input while preserving the task. `C(5,2)=10`, so even the smallest grid can realize the maximum nine marks with one source per transpose orbit. Every full cross-product is therefore constructive.

**Alternatives rejected.** Implementing all eleven baseline axes would retain redundant shape controls, palette aliases, and negative fixtures in the ordinary domain. Keeping singleton or ignored axes would continue to mislead downstream schedulers.

**Probe.** The tests cover boundary combinations in `None/easy/medium/hard`; the official override stage is green. Unknown or invalid values now raise `TypeError`/`ValueError`.

## D3 — Difficulty weights, not difficulty legality

**Choice.** All advertised values remain legal in all bands; duplicate entries only bias sampling toward smaller/sparser easy draws and larger/denser hard draws.

**Rationale.** Exact overrides should not fail because a caller changes difficulty. Weighting preserves curriculum variation without creating hidden incompatibilities.

**Alternative rejected.** Band-specific min/max domains caused the baseline’s undeclared rejection explosion.

**Probe.** The override matrix and boundary tests exercise every retained axis in all four band settings.

## D4 — Use distinct transpose orbits with empty targets

**Choice.** Select at most one member of each unordered pair `{(r,c),(c,r)}`, keep all marks off diagonal, and leave every reflected destination black.

**Rationale.** This gives an unambiguous additive-copy label: originals stay, and each new cell has a single source/color. It also makes an independent coordinate oracle simple and auditable.

**Alternatives rejected.** Occupied targets would require defining collision priority; diagonal marks are inert examples that consume teaching capacity without distinguishing the rule.

**Failure mode/limit.** This distribution does not establish behavior for collisions or diagonal-only inputs. That restriction is explicit rather than silently accepted as universal coverage.

## D5 — Refute the canonical one-sided shortcut in every draw

**Choice.** Force at least one source above and at least one below the main diagonal. Declare `upper_triangle_only` as `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, with `lower_triangle_source` as its witness.

**Rationale.** Every canonical demonstration places sources above the diagonal, so “only copy upper-triangle marks” fits all of them. A lower-triangle source is the smallest answer-changing witness. Making each pair decisive avoids relying on schedule luck.

**Alternative rejected.** Merely increasing random diversity could still yield lessons whose demonstrations all preserve the shortcut.

**Probe.** All canonical pairs fit the rival; all 64 direct regression draws refute it; the exact Racket witness is in `checks/shortcut/`; the census reports 0 ambiguous production lessons and 0 ambiguous rotations over 1,200 unique inputs.

## D6 — Exclude collinear short-line impostors

**Choice.** Require source coordinates to span at least two rows and at least two columns, and rejection-sample placement until this holds.

**Rationale.** The first repaired validator accepted 4/6 generic short-line probes, and the new regression found a real one-row generated sample. Such a specimen is rule-lawful but pedagogically degenerate and makes the validator look shape-blind.

**Alternatives rejected.** Declaring the generic line lawful would suppress a useful detector without canonical evidence. A special-case check only for the linter’s exact row would overfit the test.

**Probe.** `checks/tdd-collinear-red.log` records 3 expected failures before implementation; `checks/tdd-collinear-green.log` records 40 passes afterward; final `defect_lint` is green.

## D7 — Canonical-compatible, diagnostic validator

**Choice.** `strict_canonical_like` validates square ARC grids, size/mark/color ranges, off-diagonal distinct-orbit geometry, empty targets, and two-dimensional placement. `self_check` layers difficulty and override observations without raising on malformed grids.

**Rationale.** The baseline rejected all four canonical inputs because it demanded at least four marks; canonical support is a required ownership check. Diagnostics are more useful than exceptions for malformed review probes.

**Probe.** Every canonical input passes and the independent Python oracle reproduces every canonical output. Malformed/ragged/boolean/out-of-range fixtures return errors.

## D8 — Independent reusable review tooling

**Choice.** Add `workspace/reference_probe.py` and task-local tests under the portable `reviewer_support` layout.

**Rationale.** The probe computes transpose behavior directly from coordinates and exposes observations, teaching errors, malformed fixtures, and the canonical-fitting rival. It avoids testing production helpers against themselves and is reusable by future reviewers.

**Alternative rejected.** Importing private runner internals or hard-coding parent-depth paths would make the tests nonportable.

## Test-first record

1. Initial regression suite on the baseline: **24 failures, 13 passes**. It exposed the missing pin, canonical rejection, ignored axes, band-dependent exact controls, and absent semantic support.
2. First implementation: **37/37 passed** locally, but the full battery retained one new `defect_lint` failure.
3. Collinear regression added before code: **3 failures, 37 passes**.
4. Minimal placement/validator repair: **40/40 passed** and final battery **12/12 green**.

## Final limitations

- Ordinary grids are square, 5..12, sparse, off-diagonal, with 3..9 marks and 1..3 colors.
- No collision semantics, diagonal-only behavior, or arbitrary dense inputs are claimed.
- Semantic evidence is complete for the declared strongest canonical-fitting shortcut, not universal induction over all possible rival programs.
- Training approval remains a catalog/maintainer decision; passing review gates does not mutate approval.

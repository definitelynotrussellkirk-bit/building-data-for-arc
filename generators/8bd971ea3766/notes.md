# Working notes: 8bd971ea3766

## Selected rule and authority

Scan each row of the **original** grid. For every exact horizontal window `a,0,a` with nonzero `a`, replace the middle zero by `a`; apply all qualifying windows simultaneously and leave all other cells unchanged. `RULE_HASH = 4c32e7924ca5` pins the unchanged canonical Racket authority. The Python `rule_mirror` is covered against all three canonical labeled pairs, including overlapping windows.

## 2026-10-07 repair

Prior version `1.0.0` sampled only one clean trigger per active row, advertised dead/fictional axes, silently accepted unknown overrides, lacked a rule hash and semantic contract, could not realize the canonical five-color profiles, and encoded its narrow sampler layout into `self_check`, causing all canonical inputs to be rejected. The before battery had 6 failed stages, 1 advisory, and 5 green stages; evidence is under `checks/before/`.

Version `2.0.0` replaces that sampler with three exact observable axes:

- `grid_shape`: `4x7|5x8|5x9|6x10|8x12`
- `n_colors`: `2..4` nonzero colors
- `palette_kind`: `low|high|mixed`

Every ordinary draw embeds a translated/reflected 4x7 teaching core plus optional outer noise. The core contains:

- a row with two true targets;
- a separate row with one true target;
- an overlapping-capable exact-window rule implementation;
- a longer same-color span that must not be filled wholesale;
- unequal nonzero flanks around a zero;
- a vertical `a,0,a` decoy;
- target rows with more than two foreground cells.

Even sample indices cycle through the three canonical shape/palette-count profiles in every difficulty band; odd indices broaden shape and color-count support. Palette roles are shuffled while retaining exact override observability. Unknown, mistyped, or out-of-domain overrides are rejected.

## Semantic contract

Declared rivals are:

1. fill only the first target per row;
2. fill any zero with nonzero horizontal flanks;
3. fill every zero between repeated same-color endpoints;
4. fill both horizontal and vertical one-cell gaps;
5. fill only target rows containing exactly two foreground cells.

The generated witnesses refute all five. `horizontal_and_vertical` is also declared as a canonical-fitting shortcut because all three canonical pairs lack a decisive vertical decoy. `lesson_identifiable` rejects any lesson where a named rival fits every demonstration but changes the query.

## Verification and remaining limits

Focused task tests: 39 passing, including canonical parity, simultaneous overlapping windows, exact override observation, malformed-grid diagnostics, per-band source profiles, all witnesses/rivals, four-pair query rotations, deterministic replay, and the single-target/multi-target-row regression.

The final after battery and 300-lesson rotation census must remain source-bound to generator SHA-256 `e7bd730ca6478ab98aeda31085d91e4daf12ac4fc2645caa2624516ad1d18b29`; see `checks/after/` and `checks/lesson-census-final.json` after completion.

Known limitation: the guaranteed witnesses occupy a compact 4x7 motif, varied by palette, role permutation, translation, horizontal/vertical reflection, surrounding canvas, and noise. This is deliberately explicit teaching data, but the motif family is still narrower than the full lawful rule domain; future broadening should add independently composed witness layouts while retaining lesson-level rival checks. `self_check` intentionally requires at least one true target, so lawful no-op grids are outside this training sampler.
## Current reviewer considerations

Source SHA-256: `e7bd730ca6478ab98aeda31085d91e4daf12ac4fc2645caa2624516ad1d18b29`.

# Decisions for 8bd971ea3766

## 1. Keep the canonical authority unchanged

**Decision:** preserve the canonical Racket rule and pin `RULE_HASH = "4c32e7924ca5"`.

**Reason:** all three canonical pairs consistently implement one operation: in each original row, replace the center of every exact nonzero `a,0,a` window by `a`. The existing rule passed the before `rule_smoke`, grammar, Racket lint, and authority-sync stages. The defects were in the input generator, validator, and teaching distribution rather than the authority.

**Probe:** the new independent Python `rule_mirror` equals every canonical output and handles the overlap case `[2,0,2,0,2] -> [2,2,2,2,2]`.

**Rejected alternative:** editing Racket to match the old generator's “one isolated pair per row” layout. That would narrow the task incorrectly and contradict canonical inputs containing multiple foreground cells, multiple targets, and longer spans.

## 2. Replace the old sampler rather than preserve fictional axes

**Prior choice:** version 1.0.0 advertised grid height/width, row count, palette size, distinct color count, palette kind, position bias, density, and texture. Several were redundant, dead, unobservable, band-incompatible, or ordinary-domain aliases for negative fixtures.

**New choice:** expose only three exact controls that have direct visual meaning and deterministic observation: `grid_shape`, `n_colors`, and `palette_kind`. Validate type/value before constructing generation context and reject unknown keys.

**Reason:** an exact override is useful only if a downstream caller can request it, observe it in the returned grid, and replay it across difficulty bands. The final override stage tests all 51 cases over 4,590 draws with zero findings.

**Rejected alternatives:**

- Keep `palette_size` and `n_distinct_colors` as separate axes. Here they represent the same realized quantity and can contradict each other.
- Keep single-token `position_bias` and `density`. They are descriptions, not selectable axes.
- Keep negative fixtures in ordinary `texture`. They are useful tests but not lawful training inputs.
- Silently clamp shape overrides to a difficulty range. That makes exact controls non-falsifiable.

## 3. Preserve canonical profiles in every difficulty band

**Decision:** every even `sample_index` cycles through `(4x7, four nonzero colors)`, `(5x8, three)`, and `(5x9, four)`. Odd indices use a broader difficulty-aware shape and 2–4 colors.

**Reason:** the before generator could not reach the canonical five-color total palette and rejected all canonical inputs. Scheduling exact source profiles prevents a difficulty band from drifting entirely away from the task while leaving half the draws available for broader coverage.

**Probe:** the final profile floor accepts all 3 canonical inputs and records exact profile hits in every band; the focused test samples every band independently.

**Rejected alternative:** use only the canonical dimensions. That would repair profile support but preserve shape lock-in. The final domain also includes `6x10` and `8x12`.

## 4. Use a compact source-bound teaching core, then vary presentation

**Decision:** embed a 4x7 witness core into the chosen canvas, with random translation, horizontal/vertical reflection, palette role permutation, and optional surrounding noise.

The final core includes:

- one row with two exact targets;
- another row with one exact target and a longer same-color span;
- unequal nonzero flanks around a zero;
- a vertical same-color one-cell gap that must be ignored;
- busy target rows.

**Reason:** each feature is a direct counterexample to a plausible shortcut and is present even in the smallest source profile. Translation, reflection, role permutation, canvas size, palette family, and noise separate the rule from absolute coordinates and fixed colors.

**Revision during self-review:** the first repaired core put all guaranteed targets in one multi-target row. A new red regression showed the 4x7 profile had target counts `{row: 2}` only. Row 1 was changed from an already-filled pair to `d,0,d`, so every smallest-profile draw now teaches both a single-target row and a multi-target row. The 39-test suite then passed.

**Rejected alternatives:**

- Rely on random noise to create counterexamples. Rare stochastic witnesses do not guarantee teachability.
- Generate only one clean `a,0,a` row. That admits first-only, isolated-row, and global-color shortcuts.
- Rotate the core 90 degrees. The selected operation is orientation-sensitive; that would turn horizontal targets into vertical non-targets rather than preserve a lawful augmentation.

**Known limitation:** the witness topology remains a compact motif family. It is much broader than the old one-pair sampler but not an exhaustive composition of all lawful row arrangements. A future version should compose witness rows independently while retaining lesson-level rival checks.

## 5. Validate the true task domain, not one sampling template

**Decision:** `self_check` now verifies a nonempty rectangular ARC-color grid and at least one true horizontal target. It does not require a fixed number of endpoints, active rows, colors, or a particular core layout. `strict_canonical_like` uses the same rule-domain predicate.

**Reason:** the before validator rejected every canonical input because it had encoded exactly two endpoints per active row. A generator validator must accept lawful source examples even when the sampler chooses a narrower teaching distribution.

**Rejected alternative:** require every lawful grid to contain all teaching witnesses. Witnesses are a distribution/lesson requirement, not part of the transformation's mathematical domain.

**Limit:** lawful no-op grids with zero targets are intentionally excluded from this training sampler. They could be added later as a controlled edge-case axis after ensuring they do not dilute demonstrations.

## 6. Make shortcut hypotheses executable

**Decision:** declare five named rivals, five witnesses, witness-to-rival mappings, the canonical-fitting horizontal+vertical shortcut, and a `lesson_identifiable` hook.

**Reason:** prose claims such as “includes distractors” cannot establish that a lesson teaches the intended rule. Executable rivals answer the relevant question: can another plausible rule fit every demonstration and change the query?

**Probe policy:**

- Battery smoke: 12 materialized lessons, 4 per band, production ordering and 48 query rotations.
- Required census: 100 lessons per band, 300 total, and every one of 1,200 materialized pairs held out once as query.
- Focused tests: eight consecutive four-pair windows, every query position.

**Scope:** passing these finite named-rival checks does not prove unique induction against every imaginable hypothesis. It does prove that the five stated shortcuts are refuted under the tested production and rotation policies.

## 7. Test-first repair and retained failures

Every behavior change was preceded by a failing focused test: initial canonical/override/semantic tests failed against version 1.0.0; the later single-target-row test failed four parametrized cases against the first repair. The retained red logs are `checks/task-tests-red.log` and `checks/task-tests-single-row-red.log`. Green task evidence is under `checks/task-tests/`.

The first fully green repair battery is retained in `checks/after-v1/`; it was superseded only because self-review added single-target-row coverage. The final source-bound battery is `checks/after/`.

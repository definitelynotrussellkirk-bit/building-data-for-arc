# Working notes: 33d2674e3094

## Review repair

- Corrected the imported description from ascending to **descending** object cell area.
- Pinned the selected authority with `RULE_HASH = "9f849a344655"`.
- Replaced retrying blob growth and silent underfill with a constructive three-object layout.
- Reduced the public contract to two exact, pixel-observable axes: canvas profile and area pattern.
- Added a structural validator, exact override observer, independent Python rule mirror, semantic rivals/witnesses, and lesson-identifiability check.
- Declared the real canonical-only ambiguity: all four public pairs also fit equal-area tie breaking by ascending color.
- Scheduled tied-area counterexamples so every three-demo query rotation refutes that shortcut.
- Assigned numeric colors non-monotonically in authority order and declared both ascending- and descending-color rivals, preventing a color-rank proxy for area order.
- Added portable task-local tests and `workspace/reference_probe.py` for independent oracle, distribution audit, and direct Racket parity.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1c5f8d476ea8f590b75926cc94def1eef28983680e77b7154c35ee68d0e16751`.

# Decisions for `33d2674e3094`

## D1 — Treat the selected Racket program as immutable authority

The selected rule crops monochrome components, sorts by **descending colored-cell count**, breaks equal-area ties by bounding-box order `(top, bottom, left, right)`, top-aligns crops, and inserts one background column. The baseline’s ascending prose was changed; the authority was not. `RULE_HASH = "9f849a344655"` was added so source, checks, and later lesson evidence name the same semantics.

Rejected alternative: changing the Racket rule or explaining away the public tie examples. That would hide the generator defect and invalidate source-bound comparisons.

## D2 — Use only two public axes that pixels can prove

The public axes are:

- `profile`: `p8x13`, `p9x12`, `p10x11`.
- `area_pattern`: `tie_443`, `distinct_653`, `distinct_643`.

`observe_overrides` recovers both exactly from returned pixels, and unknown or ill-typed overrides fail immediately. The baseline axes for palette kind, blob count, density, position bias, texture, and similar fields were removed because they were constants, aliases, ignored, or not reliably observable.

Rejected alternative: retain cosmetic/dead axes to inflate combinatorial coverage. That makes override reports misleading and permits callers to believe an unobserved request was honored.

## D3 — Construct valid scenes instead of retrying random growth

Every scene is built from three known connected shapes placed without overlap or cardinal contact. Construction eliminates silent underfill and makes all legal joint overrides total. `self_check` independently re-parses pixels and enforces rectangular ARC values, a public profile, exactly three monochrome components, distinct nonzero colors, a public area pattern, no cross-object touch, and non-overlapping bounding boxes.

Rejected alternative: keep blob-walk retries and increase the retry count. That would reduce but not remove underfill and would leave exact override behavior difficult to prove.

## D4 — Make the intended semantic distinctions observable

The shapes and placements were selected so generated outputs disagree with:

- ascending cell area;
- descending bounding-box area;
- row-major scan order;
- ascending numeric color;
- descending numeric color;
- bottom-aligned packing;
- and, on equal-area scenes, ascending-color tie breaking.

Sparse shapes make cell area differ from bounding-box area. Unequal heights make top versus bottom alignment visible. Numeric colors are assigned non-monotonically in authority order, following the retained failure `checks/task-tests-descending-color-red.log` that exposed the first repair’s descending-color proxy.

Rejected alternative: random color assignment with no lesson-level check. Randomness can occasionally produce a shortcut-fitting lesson and makes failures intermittent. The chosen role permutation deterministically refutes both full numeric-color orders and the canonical ascending-color tie shortcut.

## D5 — Preserve a tie witness under every allowed query rotation

The downstream lesson policy uses four consecutive labeled pairs, of which any one can be the query and the other three are demonstrations. The schedule alternates tie and distinct patterns, so each length-four window contains two tie scenes; after any one holdout, at least one remains. Three demos are therefore enough to refute the canonical color-tie shortcut in every rotation.

The final census used 100 starts per band, period 12, and `rotation_policy=require`; both ordered production and all query rotations had zero declared-rival ambiguity. This decision is specific to a three-demo/one-query assembly. A different assembler must rerun the census under its actual policy.

Rejected alternative: generate only distinct sizes. It labels individual examples correctly but cannot teach the authority’s equal-area tie behavior and leaves the public canonical shortcut alive.

## D6 — Separate authority evidence from Python support code

`rule_mirror` is a pure task-local mirror used for validation and lesson hooks. `workspace/reference_probe.py` independently reimplements object extraction and gallery assembly, then can call the selected Racket program in a batch with no silent fallback. Final evidence contains 40 direct parity checks.

Rejected alternative: use `rule_mirror` as its own oracle. That would allow a shared bug to make the generator, hook, and test agree while disagreeing with the selected authority.

## D7 — Make label correctness part of lesson identifiability

`lesson_identifiable` first validates every demo/query input and verifies each supplied output against `rule_mirror`. Only then does it test whether declared competitors survive all demonstrations. This prevents arbitrary wrong labels from “eliminating” every rival and being falsely certified—the exact failure reproduced in audit target `5dddd8d6711e`.

## D8 — Keep failures and build reusable reviewer tools

The return retains the original 65-failure TDD run, the intermediate lint/fixture failures, and the late descending-color regression. The added test suite uses portable root discovery through the supplied reviewer infrastructure, while `reference_probe.py` gives future reviewers a reusable distribution/rival/parity audit rather than a one-off narrative.

## Remaining limitations

1. Rival coverage is finite. Passing the declared rivals does not prove universal induction.
2. The constructive shape vocabulary is small. A learner can memorize template areas instead of learning general component counting; more shape families would be the next task-local coverage improvement.
3. The public contract intentionally covers only three canvas profiles and three area multisets because those are the supported canonical profiles, not every possible descending-area gallery.
4. The tie comparator is tested through source-bound labels and generated witnesses, but only the public four-pair canonical set establishes which shortcut was canonical-plausible.
5. No downstream Qwen3.5-9B training or evaluation run was performed; this review establishes generator/lesson properties, not model-learning outcomes.

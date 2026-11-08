# Working notes: a2b749aefc65

## Base review

The supplied v3.0.1 generator already had an honest single `scene_profile` control, deterministic curriculum schedules, structural validation, broad shortcut rivals, and canonical/Racket parity. Its source remains unchanged with SHA-256 `884fc310233acb63fc20e27524007b19ffbeb3cb34766833bce078a3b2577050`; the exact canonical Racket program remains byte-identical with SHA-256 `4126da9b82909ec2ed3442a85c7bd8b43f0c5397ab595e705da49b86f76b54bb`.

The existing tests were repaired for portable reviewer replay only: legacy `scripts.*` imports and fixed parent-depth fixture paths were replaced with public `reviewer_support` and `puzzle_generators.rule_wrap` helpers. The behavioral assertions were retained, including protected-Racket same-namespace reentrancy.

## Parametric family

`travel_mode` is fixed for an episode:

- `one_step` is the exact canonical program.
- `two_steps` uses the same border-color direction decoder but advances matching markers by two cells when the two-step destination remains in the interior.

Stage A reads the four uniform side colors, decodes color to direction, and assigns each matching interior marker. The intermediate is the color-to-direction map plus every marker's source, direction, and actual destination. Stage B consumes those assignments and renders one- or two-step motion while preserving the border and unmatched distractors.

The sampler preserves the canonical boundary behavior instead of simplifying it away. Every sample has, for each side, one marker blocked under both modes and one marker that moves under `one_step` but is blocked under `two_steps`; additional freely moving markers supply density. Actual source/destination reservations are pairwise disjoint across markers and distractors, so neither setting depends on overwrite order. Every sample exercises all four decoded directions, varies the side-color permutation, supports 2–6 demonstrations and exactly four distinct queries, and ends with a substantive 30×30 query containing 24 side-colored markers and 12 unmatched distractors. The base generator's broader lesson hook still declares four examples for its many named competitors; the finite parametric lesson has only two settings and every two-demo lesson directly refutes the rival setting.

## Adversarial self-review

The primary shortcut attack replaced Stage A's decoded map with an all-up map while retaining the same two-step renderer. The retained protected-Racket witness changes the final grid, demonstrating that Stage B receives direction only through the decoded intermediate. Color permutations, four-direction coverage, matched visible inputs across settings, and explicit fully/partially blocked markers rule out fixed side-position, single-direction, setting-correlated-input, and boundary-branch deletion shortcuts. Disjoint actual reservations cover the relevant collision boundary without incorrectly requiring a blocked marker's source and destination to differ. This is finite evidence, not a universal uniqueness proof.

## Verification and limits

- Focused parametric tests: 8 passed, including exact canonical hash, all four directions, fully and partially blocked branches, cross-object reservation disjointness, and protected-Racket parity.
- Bounded adversarial probe: 12 episodes, 48 branch-checked grids, and 96 protected-Racket evaluations across seeds 0–2 and demo counts 2 and 6.
- Portable changed-target suite: 23 passed.
- Authoring preflight: all 10 canonical pairs, both settings, 24 generated labels, and 32 protected-Racket evaluations passed.
- Current witness replay: `reviewer_replayed` against the exact qualified source binding.

The inventory and receipts are ready for owner source review and native admission. They do not grant variant approval, owner acceptance, or training admission.

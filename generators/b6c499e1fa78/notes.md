# Working notes: b6c499e1fa78

## Base repair

- Raised lawful square support from 10–16 to 10–30 and retained the wall in the top half.
- Replaced legacy coercive/dead controls with exact typed controls for `grid_size`, `wall_top`, `n_openings`, `n_match`, `n_negative`, and declared textures.
- Unknown controls, booleans masquerading as integers, floats, strings, and infeasible exact overrides now fail loudly.
- Added structural role analysis and strengthened `self_check`; ordinary draws guarantee at least one clean opening match, exactly one branch-only key, and at least one surviving negative.
- Preserved the canonical Racket program byte-for-byte.

## Parametric decision

`branch_policy=matched_area` preserves both canonical reasoning branches while adding a non-collapsing sequential dependency:

- **A:** identify gray keys whose top rows fit wall openings.
- **Intermediate:** the set of their full occupied areas. Matching keys extend below the opening-height slice, so opening area and bounding-box area are wrong intermediates.
- **B:** matching keys recolor directly; a branched key recolors only when its full area belongs to that set.

The first two demonstrations use matched areas `{4,6}` with branch areas `{4,5,6,7}`, then matched area `{5}` with branch areas including `{4,5,7,8}`. This rejects match-only, branch-only, opening-area, bbox-area, first-match, parity, mod-3, between-extremes, and unlock-all shortcuts. At fixed 17×17, 21×21, and 25×25 query slots, fresh seeds vary the intended intermediate among `{4}`, `{5}`, and `{6}`; fixed intermediates retain varying mirrors, placements, wall rows, and distractors.

## Retained finding and repair

The first constructive pass used a T-shaped decoy wall opening. Its two-row shape exactly matched the five-cell plus branch's top slice, silently adding that branch to the matched-area intermediate. The retained minimal reproducer is `workspace/parametric/evidence/current/decoy-opening-regression.json`. The repair replaced that opening with an asymmetric J shape and kept exact role-profile tests.

## Final finite evidence

- Focused task tests: 18/18 passed.
- Adversarial probe: 128 ordinary base draws, 4 exact boundary profiles, 96 min/max-demo episodes, 4,992 finite rival evaluations, 24 setting-neutral checks, 24 prefix checks, crossed intermediate/dimension controls, malformed certificate/type/duplicate attacks, and 48 protected-Racket evaluations; no remaining findings.
- Authoring preflight: 4 jobs, 24 parametric labelled pairs, all 5 canonical pairs, 32 protected-Racket evaluations.
- Protected causal replay: opening-area counterfactual changes the qualified matched-area output.
- Public projection: 16 one-query views, 24 private-field invariance checks, and 4 positive controls passed.

These checks are finite and do not prove universal lesson uniqueness. Owner source reconciliation, fresh native qualification/acceptance, and any training admission remain external gates.

Owner decision: restored inherited mix weight 0 → 1 on the reviewed v4 source after fresh protected-Racket original/base-generation preflight, with no active semantic veto. See `evidence/owner-weight-recovery/current.json`; native qualification and acceptance remain the admission authority.

# Ray partition family — authoring plan and contract

Preserve the approved generator and exact canonical Racket default. Add the
private episode-fixed `region_policy` with `rays_only` and `largest_region`.
The alternative executes blue-away/red-toward rays, recomputes four-connected
zero regions on the completed grid, then paints the unique largest region 8.
This is a topology dependency rather than an independent color swap.

Rejected designs: only swapping ray direction (no new state dependency), and
selecting a fixed-side region (a coordinate shortcut). The selected design
keeps both colors on both sides, boundary stops, and multiple competing regions.

Implementation plan:
1. Write failing behavioral tests: literal ray/flood fixture, exact canonical
   source, strict count/settings validation, matched inputs, prefix stability,
   four novel queries including real 30x30 content, masked public projection.
2. Implement a task-local adapter and bounded setting-independent scene sampler.
   Use stable per-role seed streams. Keep production generator unchanged.
3. Self-review against executable rivals; retain demonstrations that reject them
   with two examples, then protected-Racket-check selected and rival labels.
4. Run focused tests and a bounded count/seed sweep, freeze the source inventory,
   qualify both settings natively, and build a source-bound causal witness.

No owner acceptance or training admission is claimed by this workspace.

## Current implementation and reproduction

`adapter.py` is self-contained; `canonical.rkt` is an exact Catalog copy.
`promotion.json` declares the native contract. Setting-neutral deterministic
streams assemble six demo candidates and four shuffled query roles, then slice
independent counts. All inputs are distinct. Ordinary shapes start at 10x10;
queries include 10x14, 17x22, 24x27 and 30x30 in seed-shuffled order. The large
scene has 24 colored seed marks, a full divider, boundary red seeds, and long
rays distributed across the canvas. The canonical production generator's
three size profiles and approval are unchanged.

Run from the outer packet folder (use a new audit output path):

```sh
python3 review.py run python3 -m pytest generators/91ba301501c5/tests/test_parametric.py -q
python3 review.py run python3 generators/91ba301501c5/workspace/parametric/audit.py --seeds 20 --out ../checks/91ba301501c5/new-audit
python3 review.py task-tests 91ba301501c5 --phase after --out ../checks/91ba301501c5/new-tests
```

`public_turn(episode, index)` is only a masking projection for the existing
controller, not a controller or training loop. No total query count, seed,
setting, program or future input appears in it. `audit.py` saves one-query
content-hashed public files and a separate private episode bundle. Labels in
that private bundle have actually been executed in protected Racket.

## Self-review and limits

The final finite bank is rays-only, smallest/first/last/input-state region,
all regions, and both-toward/both-away ray variants. Two visible demonstrations
reject every nonselected declared rule. The sampler enforces a unique maximum
and retained distinguishing examples within a 256-candidate cap. Exhaustion
raises; it never duplicates a query or silently returns fewer pairs.

A proposed bounding-box fill restricted to post-ray zero cells matched every
eligible scene in the initial 256-candidate probe. It is not counted as refuted;
that characterization does not prove equivalence outside this grammar. The
initial sampler's demand to reject this non-distinguishing rival exhausted its
cap. Replaced that demand with the genuinely different all-regions hypothesis;
its literal regression failed before implementation and then passed.

No same-side shared-column blockers, palette swaps, or 90-degree rotations are
claimed. Full red walls and partially extended red/blue branches define the
parametric input grammar. The selected region is not always a rectangle;
nonzero ray cells are preserved. Finite rival rejection is not universal
uniqueness, empirical learning benefit, or training admission. Author self-review
covered source, masking, prefixes and mutation-sensitive literal tests; no
independent reviewer facility was used.

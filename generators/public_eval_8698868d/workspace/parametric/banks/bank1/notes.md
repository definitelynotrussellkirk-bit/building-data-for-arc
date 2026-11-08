# Public parent 8698868d — current design and verification plan

Unapproved authoring work; public-parent.json remains the immutable source link.
Canonical inference: find the large tiled panel and detached smaller square
patterns against the dominant background (which can be nonzero). Count enclosed
4-connected background regions in each tile, not background pixels or 8-connected
regions. Match the loose pattern with that count, replace its background with the
tile color, inset it by one cell and crop the completed panel. Loose colors may
repeat tile colors, and zero is a valid foreground color.

Native parameter matching = component_count (canonical) or background_area.
For generated inputs both score sets have unique matches; the area setting
selects a different permutation while preserving the full matching-and-insetting
reasoning. A measures an input-dependent topological/area key; B selects a loose
pattern using that key and embeds its complete mask. No original-label lookup.

Implementation plan: tests against every official label plus hand-derived
4-vs-8 connectivity and rebasing cases first; implement Python and Racket;
construct matched inputs with 2–6 demos, independently shuffled four-query bank,
counts 0..5, sizes 6/7/8 and 30x30 stress; reject named lesson/query shortcuts;
run focused full suite, bounded Racket audit, public export checks, authoring
preflight and a protected wrong-key witness. Reuse the tested audit/witness
utilities locally, never import another task home. Owner registration and native
acceptance are separate. A finite rival audit is not universal uniqueness.


## Current result and adversarial repair

All two supplied training pairs and the test gold match the independent Python
and protected-Racket canonical rules. The default adapter program is byte-exact
reference.rkt; this new source is not registered or owner-approved.

The initial area sampler admitted a fixed count-cycle shortcut: its assignments
always mapped each positive hole-count class to the next class. A new regression
failed before the repair. Each grid now samples a feasible derangement of area
matches, and the first two demonstrations must refute an executable
cycle_components rival. Retained protected execution shows the old demonstration
matches [true,true] followed by a legal-query failure; the repaired lesson
rejects the rival in its demonstrations. Evidence: checks/public_eval_8698868d/
cycle-regression.json (10 protected-Racket evaluations). The original Racket
reference was not changed by this sampler repair.

Current direct complete task suite: 43 passed; combined two-task suite: 85 passed.
Bounded audit: seeds 0–63, 128 episodes, 2,560 count-prefix requests, 512 public
views, 11 named rivals per setting, and 304 protected-Racket evaluations on seeds
0 and 1. No findings. Stress input: 30x30, six tiles and six templates, 390 cells
differing from background, contact with all four boundaries. Its presentation
position covers all four query indices. All four queries are computed before
prefixing, with geometry independent of setting.

Authoring preflight passed both settings and seeds 17/43, using two demos plus
four queries, and every supplied official label. The wrong-metric witness uses
background-area keys [9,3,5,4,6,0]; switching to component counts changes the
selected templates and output. Protected construction and second-process replay
passed. Public export checks passed all 16 retained one-query files.

Native task-tests staging currently reports Unknown puzzle because the new home
is not registered. Direct scoped pytest and the designated authoring preflight
pass; the catalog was not edited to evade registration. Next owner action:
reconcile overlapping branches, register exact source/provenance, approve source,
refresh inventory, then run unchanged native qualification and fresh acceptance.

Limits: unique modal background; square connected frames with complete borders;
unique matching keys; templates two cells smaller than tiles. Generated instances
exercise counts 0..5, areas, colors including zero foreground, D4 orientation and
boundaries, but arbitrary broken frames or indistinguishable candidates are not
claimed. Bounded samplers fail closed rather than emit a fallback. Finite rivals
are not a proof of universal learnability. Final review was author self-review;
owner acceptance and training admission remain false.

# Working notes: cc100a8ad437

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 review

A 7,200-draw census found every positive match at `(row % template_h, col % template_w) == (0, 0)` under v3.0.0. This allowed an origin-anchored tile scan to fit all synthetic examples even though canonical examples use arbitrary offsets. v3.1.0 searches arbitrary non-overlapping windows first, requires at least two offset residues for ordinary multi-match lessons, and retains the old lattice placement only as a fallback for exact tight-packing overrides.

The generator now declares `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `lesson_identifiable`. The semantic gate verifies wildcard, original-orientation, and independent-offset evidence across difficulty bands and sliding four-demo windows.

The strict after profile policy also exposed zero canonical-scale support in medium and hard. v3.1.0 now schedules override-free canonical anchors in every band (five-cell template, two instances, canonical dimensions) while leaving all exact overrides untouched. The strict pinned census improved from 7/60 exact and 8/60 envelope at baseline to 29/60 exact and 32/60 envelope, with support in every band.

A final override diagnostic found that partial exact dimensions could randomly pair with an overlarge unspecified hard-band count. Shape size and instance count are now chosen jointly when both dimensions are exact; only unspecified axes adapt, and fully explicit infeasible combinations continue to reject.
## Current reviewer considerations

Source SHA-256: `c55416bbb797cbaccb861f14711bdd78146fec5c4bd24cd1a26f11f88dd8ba79`.

# Decisions — `cc100a8ad437`

## D1. Keep the canonical Racket rule unchanged

**Input choice / behavior:** original-orientation exhaustive wildcard matching, with cyan rectangle outlines.

**Original rationale:** executable authority and all canonical pairs agree. Prior evidence also established that template zeroes are wildcards and that the selected and archival sources are execution-equivalent.

**Alternatives considered:** rewrite Racket for style; reinterpret zeroes as literal background; allow rotations/reflections.

**Probe:** canonical execution parity, rule smoke, authority sync, literal-zero and dihedral rival outputs.

**Failure modes:** a style rewrite could desynchronize selected/archive sources; literal-zero matching contradicts executable authority; dihedral matching creates false positives.

**Decision / limitation:** no Racket change. The Python mirror is test-only and must not become output authority.

## D2. Replace origin-lattice-only ordinary placement

**Input choice:** search all legal sliding-window anchors, not only multiples of template height/width.

**Original rationale:** not documented. The lattice was likely chosen to make nonoverlap and exact-count placement easy. Randomizing only the candidate order obscured that every position still shared residue `(0,0)`.

**Alternatives considered:** randomly translate the whole lattice; jitter each lattice anchor after placement; stamp freely and repair accidental matches afterward; rejection-sample whole boards.

**Probe:** 7,200 baseline and final draws, recording every true hit modulo template dimensions.

**Failure modes:** accidental extra matches; collisions; overlapping target boxes; low success on tight boards; nondeterministic retry behavior.

**Decision / limitation:** bounded deterministic search over all windows, validating the exact exhaustive match set after every stamp. Whole-lattice translation was rejected because all matches would still share one residue and a translated-lattice shortcut would survive.

## D3. Require independent offset residues

**Input choice:** ordinary multi-match scenes must contain at least two distinct `(row mod sh, col mod sw)` residues and at least one off-origin-lattice hit.

**Original rationale:** unknown; the baseline had no such invariant.

**Alternatives considered:** require every hit to have a unique residue; require only one off-lattice hit; measure absolute coordinates instead.

**Probe:** task-local regression over easy/medium/hard and final 7,200-draw census.

**Failure modes:** an overly strong uniqueness requirement can make legitimate dense layouts infeasible; a single off-lattice hit may still leave most examples shortcut-friendly.

**Decision / limitation:** minimum two residues. This is strong enough to refute the named origin-lattice rival while remaining feasible across ordinary bands.

## D4. Keep true positive windows nonoverlapping

**Input choice:** selected positive bounding windows cannot overlap, even if their nonzero cells would not collide.

**Original rationale:** existing generator behavior and easier visual attribution.

**Alternatives considered:** permit overlaps and rely solely on exhaustive exact-match validation.

**Probe:** every candidate is checked against selected bounding boxes; final census records overlap rate.

**Failure modes:** overlapping outlines can merge and make target attribution harder; forbidding overlap reduces packing capacity.

**Decision / limitation:** preserve nonoverlap for ordinary lessons. Tight exact overrides may still use the established fallback but are exhaustively verified.

## D5. Preserve exact override compatibility with a loud, narrow fallback

**Input choice:** after 24 arbitrary-placement attempts, use the previous lattice placer only for geometries where independent offsets cannot be realized.

**Original rationale:** exact axes are a public generator contract; feasible combinations should not start failing because the ordinary curriculum improved.

**Alternatives considered:** reject every tight combination; silently clamp `n_inst`; enlarge overridden dimensions; allow overlap.

**Probe:** complete 7,722-combination matrix: 7,716 feasible successes, 6 expected incompatibilities, zero unexpected failures, four fallback-like tight cases.

**Failure modes:** fallback examples retain the old shortcut; silently changing overrides would be worse because metadata would lie.

**Decision / limitation:** retain fallback only for explicit tight overrides. Ordinary generation is independently offset in 7,200/7,200 census draws.

## D6. Add explicit named rivals instead of relying on prose

**Input choice:** literal-zero matching, dihedral matching, and origin-lattice scanning are executable rival rules.

**Original rationale:** baseline prose named some misconceptions but the semantic gate had no contract and returned `NO_CONTRACT`.

**Alternatives considered:** generic feature heuristics only; a learned model judge; hand-inspecting montages.

**Probe:** compare each rival directly with authoritative generated outputs and require each four-demo window to falsify every rival.

**Failure modes:** incomplete rival list; a rival may be extensionally equivalent on the intended domain; a buggy rival could create false confidence.

**Decision / limitation:** use simple task-specific rivals whose disagreement is directly auditable. Future reviews should add rivals when a new shortcut is found.

## D7. Keep wildcard clutter scheduled rather than universal

**Input choice:** `varied` schedule slots contain lawful non-template clutter inside a true match's wildcard cell.

**Original rationale:** directly refutes literal-zero matching while retaining clean examples in other texture families.

**Alternatives considered:** put clutter in every match; use only same-color clutter; omit clutter and depend on prose.

**Probe:** wildcard witness rate and sliding-window lesson identifiability.

**Failure modes:** universal clutter could overfit the learner to always expect noise; too sparse a schedule lets literal-zero matching survive a lesson.

**Decision / limitation:** retain the three-slot texture cycle and enforce lesson-level rival refutation. Final witness rate is about one third in each band.

## D8. Keep same-color transformed decoys universal

**Input choice:** every ordinary draw includes a rotated/reflected same-color near-miss that does not create an original-orientation match.

**Original rationale:** prior evidence showed that without it, dihedral or component-count shortcuts remain plausible.

**Alternatives considered:** different-color decoys; transformed decoys only in hard; no decoy.

**Probe:** exact match set before/after stamping, named dihedral rival, 600-draw semantic gate and 7,200-draw census.

**Failure modes:** transformed shape can accidentally contain the original shape; no free location on a tight board.

**Decision / limitation:** preserve universal ordinary witness, accepting a decoy only when the exhaustive true hit list is unchanged.

## D9. Add canonical-scale anchors to every difficulty band

**Input choice:** override-free even non-`varied` schedule slots use shape size 5, two instances, and canonical dimensions.

**Original rationale:** baseline intentionally anchored easy and broadened medium/hard, but the strict after-policy correctly treats zero cross-band support as a repair blocker.

**Alternatives considered:** declare `CANONICAL_PROFILE_OPT_OUT`; anchor only one hard seed; collapse every band to canonical dimensions; manipulate palette without matching semantic scale.

**Probe:** strict profile floor with 20 pinned draws per band; task-local scheduled-anchor regression; final census.

**Failure modes:** excessive anchoring can erase band diversity; any axis override could be accidentally ignored; profile-only matching could be gamed with wrong morphology.

**Decision / limitation:** roughly one third of ordinary draws anchor canonical scale; all overrides disable the anchor; shape size and instance count also match canonical semantics. Remaining draws preserve broad dimensions and counts.

## D10. Version and documentation

**Input choice:** bump `VERSION` from `3.0.0` to `3.1.0`, update summary/notes, add tests and a census tool.

**Original rationale:** generator RNG is version-keyed and distribution semantics materially changed.

**Alternatives considered:** leave version unchanged; document only in the review return.

**Probe:** deterministic tests, battery subject hash, return patch inspection.

**Failure modes:** version bump changes pinned random outcomes and can expose latent distribution gaps—as happened with medium canonical-profile support on the first attempt.

**Decision / limitation:** retain the version bump and repair every newly exposed strict failure rather than reverting or opting out.

## D11. Adapt unspecified axes to exact partial dimension overrides

**Input choice:** when both `grid_h` and `board_w` are exact but shape/count are not, select a feasible shape/count pair jointly from band defaults, expanding only unspecified axes to their full valid domains if necessary.

**Original rationale:** the baseline drew axes independently. With the v3.1 RNG, valid small dimension overrides occasionally combined with an overlarge random hard count and produced 15 legacy-policy rejections in the integrated override probe.

**Alternatives considered:** declare those partial combinations incompatible; clamp an explicit count; retry generation after failure; leave a nonblocking warning.

**Probe:** 90-draw regression for hard `board_w=8` and `grid_h∈{6,7,8}`, plus the 46,350-draw integrated override stage.

**Failure modes:** adapting an explicit axis would make metadata false; choosing only the smallest count could collapse override diversity; retrying after a failed draw complicates deterministic draw accounting.

**Decision / limitation:** adapt only unspecified shape/count axes before construction. Fully explicit infeasible combinations retain their loud `ValueError`.

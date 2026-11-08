# Current design and implementation plan

Parent 2c181942, immutable public-parent.json. No previous implementation exists.

Canonical inference: a four-color 4×4 hollow hub encodes two-cell docking slots at its cardinal sides. Match loose monochrome 8-connected objects by color; ignore unmatched colors. Rotate each matched object until its centered, contiguous two-cell neck faces its matching hub slot. Translate it adjacent to the slot without overlapping the hub; erase source pieces and preserve the hub and canvas. Multiple rotations are allowed only when they produce the same placed cells. This narrow grammar makes ambiguous asymmetric necks an explicit rejection rather than an arbitrary shape lookup.

Alternative: dock at the opposite spatial slot, still retaining each piece's own color. A decodes the input-dependent keyed side and determines the neck-facing orientation/translation; B consumes those placements to rebuild the scene. Color permutations and source-position randomization prevent a fixed compass/color shortcut.

Plan: independent literal/parent tests -> Python and Racket geometry -> matched sampler with 2-example rival-refuting prefix and four novel queries -> strict native adapter/private presentation -> source-bound preflight and protected counterfactual audit. Stdlib Python and task-local native resources only; no official grids or gold in executable source. All work remains unapproved authoring until owner registration and acceptance.

## Current evidence and domain decisions

All three supplied training labels and the provided test gold match the general rule through protected Racket. As the original pieces are reflection-symmetric, the examples alone do not distinguish rotations-only from arbitrary reflection. The generated family explicitly adopts rotations-only and includes asymmetric source pieces in the teaching prefix; the mirror-piece rival is refuted. Missing keyed pieces leave their hub marker untouched; unmatched source colors are erased. Duplicate loose colors, ambiguous centered neck orientations, tied modal backgrounds, out-of-canvas placements, and overlaps between docked pieces are rejected. Equivalent rotations of symmetric pieces are deduplicated rather than rejected.

Self-review found an actual grammar defect: two broad, shallow T-pieces could pass the neck test but overlap after docking. A failing regression now requires rejection before labels are emitted. All four cyclic assignments are checked, covering matching/opposite settings and direction rivals. The generated 30×30 profile also exposed a too-small content floor at seed 1 (79 foreground cells); its minimum source depth was increased rather than weakening the >80-cell test.

Current evidence is checks/public_eval_2c181942/preflight-final/ and audit-current/. The bounded audit covers 64 episodes, 640 visible pairs, 12 named rivals (768 lesson checks), 40 protected generated labels, 72 protected rival evaluations, and 64 substantive 30×30 cases. Every source bank contains four queries; both settings share inputs. The first two demonstrations refute every named rival, and source-query presentation is independently shuffled before taking any prefix. The exact preflight causal query changes 78 cells when matching-slot placements are substituted for opposite-slot placements, with protected execution and a fresh replay.

Final review is author self-review, not independent review. No observed failure remains within the admitted tested grammar. These finite checks do not prove universal lesson uniqueness. Authoring preflight is not native qualification: owner catalog registration, source review, fresh qualification/acceptance, and any training admission remain pending. Catalog-based task-tests were attempted and report Unknown puzzle; the full direct task-local suite passes.

## Current repeated-parent reconciliation

Preserve exact matching/opposite rules and current keyed docking sampler. Retain incoming portability and standalone audit improvements as source-local banks/evidence; do not invent extra rules for support-only repairs. Current evidence resides in evidence/repeat-tenth-union. Private native acceptance and root publication are separate.

# Current design and implementation

Parent `2c181942` is modeled as a keyed docking scene. A four-color hollow hub
provides two-cell cardinal slots. Loose monochrome 8-connected objects are
matched to hub keys by color, rotated until a centered contiguous two-cell neck
faces the chosen slot, translated adjacent to that slot, and stamped after the
loose originals are erased. Unmatched colors are erased. Ambiguous necks,
overlap, clipping, duplicate loose colors, and tied modal backgrounds are
rejected rather than resolved by an arbitrary lookup.

The canonical/default setting is `docking=matching` and remains byte-identical
to `reference.rkt`. The complementary setting `docking=opposite` sends each
matched piece to the opposite keyed side while retaining its own color and the
same neck-orientation grammar. Inputs are matched across settings. Presentation
shuffles a complete four-query bank before revealing one query at a time; no
setting, program, answer, future query, or total-query hint is public.

The family supports 2–6 demonstrations and 1–4 queries with stable prefixes.
The first two demonstrations refute the alternate setting and twelve executable
shortcuts, including fixed-side, mirror-piece, move/retain-source, color-map,
and malformed-placement rules. The fourth query is a 30×30 boundary case with
more than 80 non-background cells. Generated asymmetric pieces distinguish
rotation from reflection, which the supplied symmetric originals alone do not.

The sequential dependency is explicit. Step A decodes the input-specific hub
key, destination side, neck-facing rotation, translation, and final occupied
cells. Step B erases the source pieces and stamps exactly those derived cells.
Replacing the qualified opposite-slot intermediate with matching-slot
placements changes 40 protected-Racket output cells on the retained witness.

Current evidence:

- `checks/public_eval_2c181942-tests-final3/result.json`: 28/28 tests passed.
- `checks/public_eval_2c181942/preflight/`: four-job protected authoring
  preflight over both settings and seeds 17/43.
- `checks/public_eval_2c181942/audit-current/audit.json`: 64 protected-Racket
  evaluations, 130 stress episodes, and 16 sequential public views.
- `checks/public_eval_2c181942/public-export-check.json`: independent saved-file
  conformance check passed for all 16 views.
- `checks/public_eval_2c181942/causal/`: source-bound protected causal replay.

Self-review found and fixed two implementation-support defects: broad shallow
pieces that could overlap after docking are now rejected before labels, and the
task tests locate the packet root through `reviewer_support.find_root` rather
than fixed parent depth. No observed failure remains inside the admitted tested
grammar. Finite rival checks do not establish universal rule uniqueness.

This remains unapproved authoring work. Owner registration, exact-source review,
native qualification/acceptance, and any training admission are pending.

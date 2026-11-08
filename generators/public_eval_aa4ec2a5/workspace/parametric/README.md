# Topology, whole-object classification, and exterior outlining

This is a new unapproved native family for public parent `aa4ec2a5`. Root
`reference.rkt` and adjacent `canonical.rkt` are byte-identical general programs.
The adapter reads the adjacent copy; declared resources stay in this folder.
The selected generator declares literal `RULE_TASK_ID = 'ee_aa4ec2a5'` for later
owner registration. No original-grid or answer lookup occurs in implementation.

## Canonical rule and precise domain

Infer the unique modal background in a two-color input. Extract four-connected
foreground components. For each component, consider the complement of that
component within its tight bounding box; background components that do not touch
the box edge are enclosed cavities. Recolor every pixel of an object with a
cavity to 8, fill its cavity pixels 6, and leave hole-free foreground unchanged.
Add a one-cell eight-neighbor exterior outline in 2, clipped to the original canvas.
Filled holes take precedence over outlines, and foreground objects are preserved.

The foreground may have long arms, thin necks, multiple cavities, irregular
outlines and open concavities. Different foreground four-components may not touch
diagonally, and foreground nested inside another component's cavity is excluded.
These restrictions make cavity ownership explicit and exclude collective
enclosures formed by separate components. Outlines may overlap. Border clipping
is supported. The validator applies nesting exclusion under four-connectivity
for both settings, keeping the admitted input domain the same.

Input foreground/background colors vary over 0, 1, 3, 4, 5, 7, 9 and remain distinct;
output semantic colors 2, 6, 8 are fixed. The original background 4 / foreground 1
palette remains included. Exact integer grids, axes 1..30, unique modal background,
two-color inputs and all domain restrictions are checked by Python. Racket assumes
this lawful grammar; it is not a malformed-input validator.

## Parameter and input-dependent computation

`hole_connectivity` is fixed for an episode:

- `4` is canonical: an exterior path requires orthogonal background steps.
- `8` also permits diagonal background steps.

A diagonal-only aperture changes an entire object's classification, hole filling,
and exterior output, while foreground connectivity remains four and outline
connectivity remains eight. The official examples agree under both cavity
connectivities; choosing four as canonical is an explicit extension, taught in
fresh generated lessons rather than claimed to be identified by the originals.

A derives per-object enclosed-region masks and whole-object classifications.
B consumes those masks to choose the recolored foreground, filled support, and
external rim. Changing only the derived cavity lists while keeping B byte-identical
changes output. Protected observations and counterfactual replay document this
finite dependency separately from the authored interpretation.

## Construction and request contract

The deterministic bank contains six demonstration profiles and four novel query
profiles. Both initial teaching scenes combine closed and diagonally open cavities,
long arms, an open concavity, solids, small components, clipping and outline overlap.
Dense 30×30 profiles have 353/388 foreground cells; their cavity masks differ between
the two settings. Geometry is constructed directly without retries or fallback.
Each scene receives a lawful input palette and global D4 transform. The first
two demonstrations deterministically have different background colors and
different foreground colors. This prevents learned constant-color shortcuts
from fitting both required demonstrations; the two roles need not use four
distinct colors across the pair. Remaining palettes are sampled freely from the
lawful colors. The settings, demonstration and query random streams are separate.
The full query bank is shuffled before slicing a requested prefix.

Supported counts are 2..6 demos and 1..4 queries. Ordinary generation defaults to
three demos/four queries; qualification and public preflight use the supported
minimum two. Exact-integer seeds lie in 0..2**63-1. Root `generator.py` draws one
canonical input; the native adapter assembles the full teaching episode.

## Evidence status

Current outcomes, exact source bindings, finite rival limitations, and next owner
action are recorded in root `notes.md`, packet `RESULTS.json`, and the task's
`checks/` evidence. An authoring preflight is not owner qualification or acceptance.
The owner must register/review source and run unchanged native qualification and
acceptance. No approval, catalog, runtime, or training state is changed here.

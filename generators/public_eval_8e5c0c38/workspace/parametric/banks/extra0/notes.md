# Current authoring state

The default chooses a vertical reflection axis separately for each foreground
color, maximizing original same-color pixels whose reflected partner exists.
It keeps only those supported cells and erases the rest into the modal color.
Axes have doubled integer coordinates, including between-cell axes; the lowest
coordinate wins ties. This matches all two supplied train and two supplied test
labels in protected Racket, including an original tied-axis example.

The native alternative uses horizontal axes and topmost ties. Input sampling is
independent of the private setting. Reference/default program bytes and the
base/native engine bytes are pairwise identical. All input and gold files remain
unchanged. The modal-background lower-color tie convention is an explicit domain
extension; supplied and generated teaching scenes have unambiguous backgrounds.

## Grammar and adversarial teaching

Two noisy nonconvex objects and two small tied-axis glyphs use distinct colors,
random modal background, rotating locations, reflections, and random symmetric
interior pairs. Color zero may be foreground. Unmatched protrusions make box
midpoints and means wrong. Both cell-centered and between-cell axes occur.
Support is 2–6 demonstrations and 1–4 prefix-stable queries. The fourth query is
30x30 with more than 100 active cells. This four-region grammar is bounded and
does not claim coverage of every possible ARC scene or repeated-color objects.

A 64-seed audit checks 384 episodes / 2,944 labeled pairs against eleven named
rivals. No harmful surviving rival was found; this is not a universal uniqueness
proof. The default reference is broader than the generator's admitted domain.
An even-width sampling defect that removed all interior holes was fixed using
a failing regression; paired cells now vary while explicit holes remain.

## Execution and public boundary

The task suite has 65 passing tests. The task-owned original fixture is hash
pinned and provenance checked, so staged tests need no shared original data.
The self-contained generator is separately copied without sidecars and checked
for determinism, domain membership, and protected-Racket parity on six samples.
The causal witness substitutes bounding-box midpoints for measured best axes
on the same qualified authoring input and changes 82 output cells.

Sixteen one-query public views use complete-bank shuffle before projection; raw
visible bytes alone determine their IDs. The writer rejects private keys,
answers, extra queries, noncanonical bytes and duplicate IDs before writing.
Descriptions and manifests accompanying these files are PRIVATE evidence, not
model-visible input. Shared native catalog task-tests cannot address this yet
unregistered home; direct and isolated-copy pytest are used and logged instead.

## Owner handoff

Passed authoring preflight is not native owner qualification or acceptance. The
owner must register exact source/provenance, review, qualify, replay acceptance
and explicitly admit training. No shared authority or catalog was modified.
Final review here is author self-review; no independent reviewer was available.

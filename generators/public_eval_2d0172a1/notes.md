# public_eval_2d0172a1 — authoring decisions

The exact public rule extracts four-connected components of the minority color.
A component enclosing a four-connected cavity is a frame; other components are
blobs. For each axis, frames contribute singleton events at their bounding-box
endpoints and blobs contribute their entire projected interval. Merge overlapping
intervals transitively, including endpoint contact, sort the groups, and map them
to coordinates 0, 2, 4, ... . Draw rectangular frame outlines and single-cell
blobs. The canvas includes a one-cell halo around each blob, so an exterior point
can leave a trailing background row or column. Four training and two gold query
pairs establish the original default.

The episode-fixed frame_policy is all|outermost. The default retains all frames;
outermost removes frames inside another frame's actual cavity before constructing
coordinate events, while retaining every blob. Stage A classifies and selects
input components. Stage B consumes that selection to form interval groups,
assign coordinates, and draw the compact diagram. Dropping a selected component
before layout is the intended source-bound causal intervention.

The supported grammar uses two distinct colors with a strict background
majority, exact integer grids of size 5–30, four-connected components with at
most one cavity each, and noncollapsed frame endpoints. Compact outputs must
also stay within 30×30. Empty frames, singletons, diagonal foreground separation,
and transitive interval chains are explicitly taught extensions. Multiple holes,
tied color frequencies, collapsed projected frames and oversized outputs are
rejected. The sampler uses rounded orthogonal contours and connected hole-free
blobs, nested and disjoint frames, varied colors, reflections and transpositions.
It does not claim unrestricted curved-shape or topological-layout uniqueness.

A retained seed-0/profile-5 sampler counterexample showed that a two-cell corner
cut could join a child blob and create multiple cavities. Sampled cuts now stop
at one cell, preserving the planned two-cell child clearance. The focused
regression and original failing grid/source hash are retained in the return.
The profile-9 stress scene also exposed a projected-frame collapse: two exterior
three-cell blobs bridged the narrow empty frame's endpoint events. Those blobs
are now aligned singletons; the frame remains empty and its endpoint groups stay
distinct. The admission rejection and actual pre-repair geometry are retained.

The direct protected bridge accepted the first Racket source, but ArcExecutor's
AST serializer turned a quoted empty-list accumulator into a quoted expression.
That made interval merging fail before the first label. The task-local source
now constructs the empty accumulator with `(list)` in all three program copies.
The actual failing original, translated form, old source hashes and a two-setting
portable Executor regression are retained. Shared runtime code is unchanged.

The initial two-demo core had only two nesting levels and sometimes exposed
halos on only one side. Concrete rivals could remove just innermost frames or
pad just the leading/trailing side, fit both demonstrations, and change queries.
The first demonstration now has three nesting levels, an empty innermost frame,
and exterior singleton points at both low and high extremes on both axes. It
also retains the column-span chain and diagonal separation. The second teaches
row-span chains and multiple outer frames. The four query profiles and programs
are preserved by this teaching repair. Original witnesses remain under checks/.
Four distinct shuffled queries include triple nesting, empty inner frames,
exterior halos and substantive 30×30 drawings. The supported minimum is two:
the 24 frozen rivals plus one explicitly post-exposure depth rival leave no
demonstration-fitting, query-changing survivor across eight audited episodes.
Some alternatives remain equivalent on these sampled queries; this is not a
universal identification claim. Seventy independent inputs under both policies
match all 140 labels through native ArcExecutor after the initializer repair.
The report preserves the earlier 140 Python comparisons, 80 count-prefix checks,
and teaching audit by their exact unchanged resource hashes. Sixteen query inputs
and 32 query labels are unchanged across the demonstration repair. Root
generation is input-only and independently relocatable.
The adjacent sampler and canonical program are exact copies of the root files.
Owner registration, source approval, qualification and acceptance remain pending.

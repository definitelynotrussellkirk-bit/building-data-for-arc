# public_eval_136b0064 — current authoring decisions

The supplied parent has three training pairs and one provided test gold. A
full-height yellow separator divides a grid of 3×3 glyphs from a blank canvas
with one gray cursor. Read glyph columns from left to right and each column
top to bottom. Each instruction begins one row below the previous endpoint:
the four masks mean right three, left two, left four, or down two, painted in
the glyph's ink. Horizontal strokes include the prior cursor column; their
endpoint displacements are therefore +2, −1, and −3. Retain the full canvas.

Author the general shape-codebook interpreter and verify all four original
labels. Shape and color are confounded in those originals; interpreting shape
as opcode and color as ink is a documented generalization taught with remapped
colors in generated examples, not a uniqueness claim about the supplied data.
Use `scan=columns|rows`, preserving the exact authored reference as default.
Stage A decodes and orders the input-dependent instruction sequence; B executes
it with a cursor whose state changes after every command.

The generated grammar admits 1–4 glyph columns, 3×3 slots separated by zero
gaps, optional empty slots/padding, and any ink 1–9 except separator 4. Ink 5
on the program side is lawful; only the right canvas determines the marker.
Grid height is 3–30 and total width at most 30; canvas width is at least four.
Require every generated program to remain in bounds under both scan orders.
This matched generated domain is narrower than the original column interpreter:
the first original training grid and supplied test grid leave the canvas under
row order. Their canonical column answers remain valid and are checked directly;
executing one setting never requires another setting to succeed on an original.
Construct three teaching demos, optional prefixes up to six, and four queries,
including a one-command minimum and a 30×30 program with 21 instructions.

Keep the root input-only generator self-contained. Check strict parsing,
original and generated protected labels, independent rival programs, count and
marker boundaries, exact authoring preflight, causal replay and private/public
exports. Owner registration, qualification and acceptance remain separate.

## Final result and retained repairs

All 78 focused tests pass (38 core tests and 40 independent tests). The frozen
40-rule bank has no query-changing demo-fit survivor across 64 episodes and
448 independently checked labels. Its 66 protected executions match all four
official labels, 34 hand labels and 28 generated labels. A separate fresh
19-hypothesis review also passes, including 50 protected executions and an
isolated root-only generator import. These are bounded checks, not a claim of
unrestricted rule uniqueness.

The bank found a real teaching gap at row-setting seeds 6 and 8: snake reading
fit all three demos but changed queries. A standalone wrong Racket rule and
minimal 7×12 counterexample are retained. The last odd-row glyph in demo 2 now
gets a different ink from its first glyph if their inks would otherwise match.
This changes eight demo-2 pairs across the 64 audited episodes and eliminates
the shortcut. All 256 query pairs, 192 optional-demo pairs and 128 demo-0/demo-1
pairs remain byte-identical. Six protected changed-example executions pass.

Dropping the third demo admits first-two-columns and cursor shortcuts, plus
snake reading in row mode, at seeds 0 and 17. The third demo rejects them. This
supports three demos for the current curriculum, not an impossibility theorem
for every conceivable two-demo curriculum. A singleton first demo was chosen
before implementation to avoid a command-count gate.

The base hook returns `[]` on valid generated inputs and findings strings on
invalid inputs, as required by the native worker. `AXES={}` declares no caller
overrides; seeded diversity remains documented in the README. Initial strict
parser and canonical-domain failures, plus the snake and hook regressions,
are retained alongside their successful repairs.

Native authoring preflight checks all four original labels and both settings
at seeds 17 and 43. The protected length-ablation witness replays, and all 16
actual one-query public views pass the projection audit and independent public
checker. This family is reviewer-ready; owner registration, source review,
native qualification and acceptance remain pending. No training admission.

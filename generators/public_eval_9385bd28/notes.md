# Public parent 9385bd28

## Canonical rule

Find the connected two-column color key. Each row maps the left color to the
right color. Apply rows from bottom to top. For a mapped source color, take all
matching scene cells outside the key and their common bounding rectangle.

- A target of zero or the modal background restores the original input inside
  the rectangle, so this row acts as a transparent cutter.
- Otherwise fill the rectangle with the target color. When the source consists
  of multiple disconnected fragments, restore those source fragments over the
  fill; a single solid source object is replaced.

The root `reference.rkt` matches all four public demonstrations and both supplied
test gold labels under protected Racket.

## Episode-fixed extension

`finish=highlight_largest_change` performs the complete canonical composition,
forms 4-connected components from the cells whose visible value changed, and
recolors the unique largest such component to 9. The sampler makes the largest
raw rectangle lose after a later transparent cut, so the second stage cannot be
reduced to pre-composition rectangle area.

The family is reviewer-ready only. Owner registration, unchanged native
qualification, exact-source acceptance, and any training admission remain
separate gates.

Owner reference serialization correction: strict parsing exposed one extra closing parenthesis after each complete rule. Removed only that unconsumed character, preserving the parsed executable form. Original bytes and hashes are in evidence/strict-racket-serialization/repair.json; fresh protected execution and native acceptance determine current readiness.

## Current repeated-parent reconciliation

Preserve exact combine-only and highlight-largest-change programs and incumbent broad key/source-fragment parser. Add bottom-priority composition via the incumbent parser, preserving transparent restoration and fragment semantics. This is a semantic port of the incoming priority idea, not its different background-overwrite rule. Add incoming multi-rectangle constructor. Current evidence resides in evidence/repeat-eighth-union. Private native acceptance and root publication are separate.

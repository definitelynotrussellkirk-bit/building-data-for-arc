# Visible-examples-only solve notes

## Scope and exposure

I received an isolated solve assignment with no supplied rule or reference context.
I read only this episode's `README.md` and `challenge.json` before writing my own
`solution.py` and these notes. I have not opened the generator, Racket rule,
canonical data, reference solutions, earlier explanations, parent reports, or
private/query answers. Packet-level earlier exposure must be recorded as **yes**
because the root reviewer had previously reviewed the generator; that exposure
was not supplied to this isolated solve agent. Reference consulted: **no**.

## Observations and hypothesis

Every visible output has the input's dimensions. The retained cells preserve
their coordinates and colors, while the other foreground cells become zero.

My first candidate hypothesis is: partition nonzero cells into monochromatic,
orthogonally connected components; delete every component with a cell on any
outer border; preserve all remaining components.

Evidence from visible inspection:

- Example 0 removes the top-border color-6 square and bottom-border color-1
  shape, preserving the interior color-8 square.
- Example 1 removes the left-border color-4 and color-1 components and the
  right-border color-5 component. It preserves the separate interior color-5
  component and the interior color-6 singleton.
- Example 2 removes the top-border color-1 and bottom-border color-5 shapes,
  preserving the interior color-3 square.
- Example 3 preserves the interior upper color-6 component and color-9
  singleton, while removing the color-6 components at the left and bottom
  borders and the color-8 component at the right border.

The following are reasoning comparisons, not executed candidate attempts:
removing an entire color would contradict the mixed retained/deleted color-5
and color-6 occurrences in examples 1 and 3. Connectivity that ignores color
would join kept interior cells to discarded border objects. Diagonal
connectivity would join the two upper color-6 components in example 3, which
are treated differently in its output. Thus the visible distinctions support
same-color, four-neighbor connectivity.

## Implementation and experiment log

### Revision 1

Implemented the first candidate as a flood fill over each same-color,
four-connected nonzero component. The output starts at zero and receives only
components without a border cell. There was no earlier implementation or
executed failed attempt.

Planned visible-only check, working directory
`/workspace/scratch/b924d53d1914/packet/WORK`:

```sh
.venv-review/bin/python ../review.py solve check --intent solve --note 'First candidate: retain monochromatic four-connected components only when none of their cells touch the outer border; examples 1 and 3 distinguish color-aware and orthogonal connectivity.'
```

The check result will be recorded after execution. No private query correctness
will be requested or inspected.

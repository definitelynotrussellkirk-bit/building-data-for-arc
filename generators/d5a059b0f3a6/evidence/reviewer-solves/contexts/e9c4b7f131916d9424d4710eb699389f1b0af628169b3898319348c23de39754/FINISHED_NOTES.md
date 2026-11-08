# Blind solve work log

Task ID: `blind_solve_d5a059b0f3a6`

## Access boundary

I started with no earlier exposure to this task. I inspected only
`solve-blind/challenge.json` as puzzle evidence. I did not open any generator,
Racket rule, reference solution, private label, old explanation, or audit record.
The provided `solve_episode.py` commands are used only as the authorized blind
checking/finishing interface; its implementation was not inspected.

The challenge contains **3 visible training pairs** and **2 masked test inputs**.
Both test cases have input only. Their correctness cannot be established from
this file.

## Inspection and hypotheses

1. I initially printed the JSON with indentation. That output was too large and
   was truncated, so I immediately reread the same file as compact grid rows,
   input/output dimensions, and color counts. This was an inspection correction,
   not a solver revision.
2. All grids have background 0, blue pattern/noise cells 1, and one other color
   forming four three-cell L corners for each rectangle. Visible marker colors
   are 2 and 8; masked inputs use 7 and 5. Every visible output preserves all
   marker cells at the same locations and with the same colors.
3. Blue cells outside the corner-defined rectangles disappear. Within each
   rectangle, the original blue cells remain, and a reflected copy is added.
   No visible blue cell inside a rectangle is removed. Thus there is no visible
   basis for filtering supposed interior noise.
4. I considered whether rectangle aspect ratio selects the reflection direction.
   It does not: training case 1 has a 7-row by 8-column rectangle whose pattern is
   copied from the top to the bottom. Source placement is the relevant feature.
5. A read-only Python probe enumerated all rectangles by matching the twelve
   corner marker cells, collected their blue cells, and compared row-reflection
   and column-reflection candidates to each visible output. Exactly one candidate
   matched for each of the **10 training rectangles**. The probe also printed
   blue bounding boxes and their displacement from the rectangle center.
6. A delegated independent reader, restricted to the same challenge file,
   observed a sharper geometric criterion: for exactly one of the two center
   lines, all blue source cells lie strictly on one side. Reflect across that
   line. This criterion is unique in all 10 training rectangles and all 7 masked
   input rectangles. I adopted that criterion for the initial implementation.

## Visible rectangle evidence

Coordinates below are zero-based, inclusive, and ordered
`(top, left, bottom, right)`. A row reflection copies top/bottom; a column
reflection copies left/right.

| Training case | Rectangle | Source blue count | Observed reflection |
| --- | --- | ---: | --- |
| 0 | (4, 12, 10, 24) | 6 | Columns |
| 0 | (10, 5, 17, 9) | 3 | Rows |
| 0 | (15, 18, 26, 25) | 10 | Rows |
| 0 | (22, 3, 27, 11) | 4 | Columns |
| 1 | (2, 2, 8, 10) | 3 | Columns |
| 1 | (14, 4, 20, 11) | 4 | Rows |
| 1 | (15, 14, 21, 22) | 4 | Columns |
| 2 | (1, 2, 7, 8) | 3 | Columns |
| 2 | (2, 16, 8, 22) | 5 | Rows |
| 2 | (14, 5, 22, 11) | 3 | Columns |

The visible output blue counts are 46, 22, and 22. The respective input blue
counts are 36, 21, and 21; 13, 10, and 10 of those cells are outside the frames.
The inferred rule doubles the retained in-frame counts of 23, 11, and 11.

## Solver revision 1

I wrote `solution.py` with one initial implementation:

- Find rectangles by all four L corners in any color other than 0 or 1.
- Require that the twelve expected corners are the rectangle's only marker
  cells. This prevents accidental combinations of corners across frames.
- Start with the original grid with all 1 cells cleared, preserving markers.
- For each rectangle, restore its original blue cells and add their reflection
  across the unique center line placing the entire source on one side.
- Do not overwrite a marker with a reflected blue cell.

There is an explicit fallback for a hypothetical rectangle where both or neither
center line separates the source: reflect in the direction of larger bounding
box center displacement. No visible or masked input needs this fallback, so its
behavior is unsupported by the examples. The implementation otherwise assumes
the observed meanings of 0 and 1 and the observed twelve-cell corner format.

I have not manufactured a failed implementation or an artificial revision.
The aspect-ratio idea was rejected during inspection, before writing the solver.

## Check and finish record

The first and only solver revision was checked from the packet root with:

```sh
python3 solve_episode.py blind check --intent solve --note 'Initial hypothesis: preserve corner frames, erase exterior blue cells, and mirror each interior pattern across the unique center line placing all source cells in one half; supported by all ten visible rectangles.'
```

The command completed successfully and reported revision 1, **3/3 visible
examples passed**, `reported_label: unknown`, `verification: reviewer_local`, and
`training_admitted: false`. No mismatch required a code revision. The check did
not disclose masked-query correctness.

I am stopping because the first implementation passes every visible example and
the reflection-axis criterion is unique in every masked input. Further tuning
without additional labeled evidence would be unsupported. The finishing command
is:

```sh
python3 solve_episode.py blind finish --earlier-exposure no --reference-consulted no --reason 'The first solver revision passes all three visible examples; the inferred reflection axis is unique for all ten training and seven masked-input rectangles. No additional labeled evidence is available, and masked-query correctness remains withheld.'
```

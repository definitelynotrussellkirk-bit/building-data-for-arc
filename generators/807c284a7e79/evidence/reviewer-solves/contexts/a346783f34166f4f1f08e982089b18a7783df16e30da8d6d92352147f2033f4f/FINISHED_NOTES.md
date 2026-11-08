# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.


## Exposure declaration and scope

This is a fresh solve for task 807c284a7e79. Before solving, I had no exposure
to this task's Racket rule, generator, canonical ledger, reference solution,
private labels, audits, prior solve explanations, or other round directories.
I read only the public solve README, challenge.json, the initial solution.py
stub, and this initial notes template. I also read the generic
using-superpowers skill, whose subagent instruction says to ignore it; it
provided no puzzle information. All puzzle evidence used below is public.
This is a work log of hypotheses, probes, and decisions, not a token-level
reasoning trace.

## Public observations

Each input contains walls of color 8, empty cells of color 0, and one marker of
color 2. In the outputs, walls stay unchanged. The marker becomes color 3;
reachable open cells alternate colors 3 and 4. In train 0, the gap in the
vertical wall connects both sides, and both sides are colored. In train 1,
the complete horizontal wall leaves the upper region unchanged. In train 2,
the complete vertical wall leaves the right region unchanged. These examples
support four-neighbor connectivity through colors 0 and 2.

## Probe 1: connected component and checkerboard phase

Ran a Python stdin experiment with WORK/.venv/bin/python3 from the packet root.
It read challenge.json only, flood-filled the marker's four-connected open
component, and compared three actual candidate predictions: phase aligned to
the marker, phase aligned to the lexicographically first component cell,
and fixed global even row-plus-column parity. The command exited 0.

Observed training results, with mismatch counts in the order marker / first
component cell / global-even:

- Train 0: marker (7, 9), first cell (1, 1), 58 reachable cells; 0 / 0 / 0
  mismatches. Marker-phase colors: 30 cells of color 3, 28 of color 4.
- Train 1: marker (7, 2), first cell (6, 1), 24 reachable cells; 0 / 0 / 24
  mismatches. Marker-phase colors: 12 cells of each color.
- Train 2: marker (6, 4), first cell (1, 1), 42 reachable cells; 0 / 0 / 0
  mismatches. Marker-phase colors: 21 cells of each color.

The fixed global-even candidate is ruled out by train 1. The marker-aligned
and first-cell-aligned candidates agree on all three training examples, so
visible training labels do not distinguish them. Reading only the public
query inputs, query 0 has 42 reachable cells and query 1 has 14; the two phase
conventions produce opposite colors on those cells. No query output labels
were accessed.

## Revision 1: marker-seeded alternating flood fill

Implemented solve(grid) using breadth-first traversal from the unique red
marker. The marker and cells at even shortest-path distance become 3; cells
at odd distance become 4. Traversal is limited to four-neighbor cells whose
input value is 0 or 2. Other cells are preserved, and the input is copied.
This assigns a direct role to the marker as both the component selector and
the starting color, consistent with its becoming 3 in every training output.
The implementation has not been replaced by another revision.

Remaining uncertainty: a checkerboard anchored to the region's first cell
also fits every visible training output but differs on both public queries.
I choose marker-seeded distance parity because the sole red cell gives an
explicit starting point; I cannot resolve this ambiguity using unavailable
private labels. All provided inputs have one marker and rectangular grids;
behavior outside that evidence is not established.

Next actual step: run the required public blind checker for revision 1.


## Required public check and stopping decision

The actual revision-1 blind check used review.py blind check --intent solve
with the marker-distance hypothesis in --note, from the packet root using
WORK/.venv/bin/python3. It exited 0 with execution_status completed,
visible_passed 3, visible_total 3, and reported_label unknown. The check's
program hash was cb6f7e19ff85da5eacd83badc87371592d654867257309eb69f85fa5c9913a36.
The exact command array, cwd, exit code, feedback, and public hashes are
recorded in WORK/checks/blind-commands.json.

No implementation revision was warranted by that feedback. There has been
one official check, and no failed official check or replaced implementation.
The competing first-cell phase remains unresolved by public labels and is
not presented as disproved. I am stopping because the selected general rule
matches all visible examples and the permitted checker withholds private
query correctness. I have not inspected any private or reference material.

The finish command will declare earlier-exposure no and reference-consulted
no. These declarations are true for this solve. This notes file will not be
edited after finish; its outcome belongs in the separate command record.

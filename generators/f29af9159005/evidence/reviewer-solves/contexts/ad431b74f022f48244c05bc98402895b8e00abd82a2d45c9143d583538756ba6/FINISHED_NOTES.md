# Solve work log

## Exposure and allowed material
I have no earlier rule exposure. I read only this directory's README.md,
challenge.json, initial solution.py, and initial SOLVE_NOTES.md. I have not
consulted generator source, a Racket rule, reference solutions, private labels,
audit material, or previous solves.

## Revision 1: cardinal rays from red seeds
Training examples 0 and 2 add yellow (4) only between the red (2) and the
nearest blue (1) on each of its four cardinal directions. Blue cells and
unrelated blue distractors stay unchanged. Example 1 has no aligned blues,
and its complete red row and column become yellow except for the red seed.
Thus each red emits rays toward the four edges, stopping before blue cells.
The implementation reads obstacles from the original grid and paints only
background cells, preserving the existing nonzero colors.

The visible queries contain TWO red cells, while each training example has
only one. This is a real underdetermination: training cannot establish
whether all red cells or a distinguished red cell should emit rays. I use the
natural independent-seed extension: every red emits all four rays and outputs
are combined. Rays pass through other red cells without recoloring them.
Stopping at another red would give the same union for these two queries,
because both seeds share a column and no blue is in that column. A rule that
selects only one red remains observationally possible from training.

Planned probe: run the authorized visible checker once with this hypothesis.
There is no invented negative result or previous failed implementation.

## Visible checker result and stop decision
Executed from packet root:
`python3 review.py blind check --intent solve --note 'Four cardinal yellow rays from every red seed, stopping before blue cells or at the edge; multiple seeds are an explicit extrapolation from single-seed training.'`
Exit code 0. Returned revision 1, execution_status completed,
visible_passed 3 / visible_total 3, reported_label unknown, and
training_admitted false. Private query correctness is withheld. No genuine
failure occurred. I am stopping after this successful visible check because
another identical check would not distinguish the multiple-red alternatives.
The final candidate implements the documented natural extension, with its
uncertainty retained above.

Finalization command:
`python3 review.py blind finish --earlier-exposure no --reference-consulted no --reason 'All 3 visible examples passed with cardinal rays from every red; multiple-red query behavior is an acknowledged extrapolation, and further visible checking cannot resolve it.'`

# Working notes: 8862d66fbb3d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native parametric admission review — 2026-10-25

Built `workspace/parametric` with exact canonical setting `all_overlap` and
sequential setting `adjacent_overlap`. Step A transforms the right panel by the
command and intersects it with the left panel. Step B keeps only cells with an
orthogonal neighbor in that command-dependent intermediate. The retained
`wrong_left_intermediate.rkt` counterfactual instead measures adjacency in the
raw left panel and changes the final protected-Racket output.

The generator supports two through six demonstrations and one through four
prefix-stable queries on identical inputs across settings. Its 4x7 input and
3x3 output are an intentional exact-authority boundary: the canonical Racket
program hard-codes those dimensions, so a 30x30 case would violate exact default
preservation. `workspace/parametric/audit.py` provides reusable structural,
public, teaching, protected-Racket rival, and causal checks for future agents.

Bounded review evidence is in `workspace/parametric/evidence/current/`; native
qualification and owner acceptance remain separate authority steps.

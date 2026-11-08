# Solve notes

## Scope and exposure

This is a separate worker solve stage. I read only the public solve README and
challenge.json for puzzle evidence. I did not consult the generator, Racket
rule, reference solution, private labels, hidden query answers, earlier solution
notes, or task tests. The required general Superpowers entry guidance was read;
it explicitly exempts dispatched subagents from its workflow.

The coordinating reviewer had seen task references before this separate solve
stage. Therefore the whole post-repair solve record must be classified as
**exposed**, even though this worker's puzzle-solving context is clean. The
finish declaration is earlier-exposure=yes, reference-consulted=no. This is not
an uncontaminated whole-session solve claim.

## Visible observations

- Training example 0 has a color-1 frame spanning rows 7–11 and columns 4–7.
  Its 3-by-2 interior is zero. The output adds the same frame at rows 10–14,
  columns 8–11, around an already zero 3-by-2 interior.
- Training example 1 has a color-5 frame spanning rows 4–7 and columns 15–19.
  Its 2-by-3 interior is zero. The output adds that frame at rows 4–7,
  columns 9–13. A smaller color-2 3-by-3 frame remains unchanged.
- Training example 2 has a color-6 frame spanning rows 14–20 and columns 11–14.
  Its 5-by-2 interior is zero. The output adds that frame at rows 8–14,
  columns 16–19.
- All other visible cells are preserved. The source frame's color is different
  across examples, and its dimensions vary, so neither is a fixed parameter.

## Revision 1 — initial hypothesis and implementation

Hypothesis: identify the largest complete monochrome nonzero rectangular frame
with an all-zero interior. Use its color and interior dimensions to draw a
matching border around every all-zero rectangle of that size that has room for
the border. The original template already satisfies this condition, so painting
it again preserves it. The smaller frame in example 1 is a distractor because
the larger template is selected.

The implementation enumerates complete frames, chooses the maximum outer area,
then finds matching zero interiors using only the original input. It copies the
grid and changes only the computed border cells. It contains no stored example
outputs, fixed coordinates, query labels, or task-data reads.

This is the first actual code revision. No failed revisions or experiments
preceded it. The prescribed visible checker is the only execution test planned.
The first check will determine whether the literal inferred rule matches all
three visible outputs and executes on the two masked queries. Query correctness
remains UNKNOWN regardless of execution success.

## Limits of the evidence

The examples support selecting the larger frame over a smaller distractor and
matching its unrotated dimensions. They do not establish a tie policy for equally
large source frames or a different rule for several congruent empty regions.
The implementation applies the same matching rule uniformly to every candidate;
it does not introduce coordinate-specific exceptions.

## Observed check result and stopping decision

The prescribed check for revision 1 completed with exit code 0 and reported
visible_passed=3, visible_total=3, execution_status=completed, and
reported_label=unknown. There is one actual code revision and one checker run;
there were no failed revisions. No further code changes or tests were made.

Because the uniform hypothesis matches every visible output, I stop here and
retain masked-query correctness as UNKNOWN. The finish command records
--earlier-exposure yes --reference-consulted no for the exposure distinction
explained above.

The checked program hash is
1ec23c415192468b4e505a8d7e5db6240a581bc3a7aa6f6c2bf0cbe36e730152.
The checker supplied the source binding without exposing source contents:
generator_hash=44637c626bd95413b08cf1a4620a026c2b1f6e792faee54969a52d3580bfd99e;
instance_hash=23b7449f39e39233b7e903ceebf0f125446fe3389660539c0dfa5a813c6a89a5.

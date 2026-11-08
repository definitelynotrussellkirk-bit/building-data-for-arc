# Post-repair visible-only solve notes

## Source boundary and exposure declaration

This solving agent was started in a fresh isolated context. Its task message supplied
administrative instructions and the expected generator hash, but no rule or previous
solution explanation. I ran `python3 review.py solve prepare` and read only the newly
prepared `WORK/solve/README.md` as task evidence. I did not open the generator, Racket
rule, reference solutions, canonical data, private labels, prior solution notes,
audits, or answer-bearing helpers. The preparation/check harness may execute its
own machinery; I have not inspected its source.

The broader post-repair session has already inspected the rule, as explicitly
reported by the parent agent. Therefore the truthful episode declaration is
`earlier-exposure yes`, even though this isolated solving agent did not itself
receive or read that rule. The declaration `reference-consulted no` applies to
this solving episode. This is a separate episode from the earlier finished blind
solve; no earlier solve artifact was consulted.

## Visible observations

All three training examples contain solid, axis-aligned, uniformly colored
rectangles on a zero background. Dimensions and positions stay fixed. Each
rectangle keeps its complete outermost border. Its interior becomes a checkerboard
of the rectangle's original color and zero, with zero at the top-left interior
cell. The phase restarts independently at each rectangle's own top-left corner.

Evidence from the visible examples:

- Example 0: the 3 by 6 orange rectangle loses two alternating cells in its only
  interior row; the 4 by 3 cyan rectangle loses only its first interior cell.
  The 7 by 7 blue rectangle loses 13 interior cells in alternating 3/2/3/2/3 rows.
- Example 1: the 6 by 6, 6 by 7, and 5 by 7 rectangles lose 8, 10, and 8 cells,
  respectively. Their borders remain intact and the interior phase is the same.
- Example 2: the 3 by 4, 4 by 5, and 3 by 3 rectangles lose 1, 3, and 1 cells,
  respectively. The 4 by 5 rectangle's two interior rows alternate 2 then 1 holes.

The natural general rule inferred from these visible pairs is to erase interior
cells whose row and column offsets from the rectangle's top-left corner sum to
an even number. All other cells stay unchanged.

## Revision 1 and experiment plan

I wrote one implementation. It finds same-color, four-connected foreground
components, derives each bounding box, and erases the indicated component cells
strictly inside that box. It starts from a copy of the input and does not mutate
the supplied grid. The visible inputs support rectangular components; no claim
is made about arbitrary nonrectangular objects outside that demonstrated domain.

I will submit this actual revision with `review.py solve check --intent solve`.
No alternate implementation, failed execution, or hypothesis trial preceded this
revision. The official checker is the only correctness experiment planned. Its
feedback is limited to visible training examples and execution of the two query
inputs. Private query outputs remain unknown and no hidden correctness claim
will be made.

## Check 1 result and stop decision

The actual revision was checked once using `python3 review.py solve check
--intent solve --note ...`. It exited 0 and reported revision 1,
`execution_status: completed`, `visible_passed: 3`, and `visible_total: 3`.
The returned program hash was
`0004684b82227cf589a679870a74c96d730a9751f3d61ae5f5035dda5d58874b`.
The reported query label was `unknown`; query correctness is not established.

No failed checks, alternative revisions, or additional experiments occurred.
No code changed after this check. This result supports stopping because the
single visible-example hypothesis matches every supplied training pair and the
checker completed execution. Private query outputs remain unconsulted.

The finish declaration will record earlier rule exposure as yes for the broader
session and reference consultation during this isolated solve as no, for the
reasons detailed above. Exact command arguments, exit codes, and evidence paths
are retained in `agent_receipts.json`.

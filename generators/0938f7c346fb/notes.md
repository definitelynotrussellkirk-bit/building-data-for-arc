# Working notes: 0938f7c346fb

## 2026-10-24 reviewer decision

Built a native two-setting family around the existing sequential rule rather than
changing the approved production generator. `query_operand_order=xy` is the exact
canonical Racket source; `yx` changes only the final application to use `Y,X`.
Both settings share the same generated inputs and remain total on the same
five-panel grammar. A directional `left-minus` demonstration identifies the
setting even at the minimum of two demonstrations.

The generator's old test fixture assumed a fixed checkout depth and failed in the
portable staged runner. It now locates canonical data with `reviewer_support`;
the complete task suite passes.

A finite demonstration-only audit checked 13 candidates per episode (both order
rules, eight fixed-operation shortcuts, X/Y copies, and zero) over seeds 0/17,
demo counts 2/3/6, and both settings. The selected rule was the sole survivor in
all 12 cases. This is bounded evidence, not a universal uniqueness proof.

Native qualification executed both exact Racket programs on seeds 0 and 17 with
3 demonstrations and 4 queries, including the substantive 30x29 stress input.
The protected-Racket causal witness replaces the inferred `left-minus`
intermediate with `xor`; both settings change final output. Public projection was
also checked with four masked query outputs and hash-named exact bytes.

Next action: integrate these exact bytes, rerun owner qualification and witness
replay, then perform native acceptance. Reviewer-ready is not owner-accepted and
no training data is admitted by this return.

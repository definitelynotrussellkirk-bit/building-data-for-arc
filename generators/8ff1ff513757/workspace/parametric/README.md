# Row-compression contact relay

The native family preserves the exact canonical `compress_only` program and
adds `mark_vertical_contacts` over the same inputs.

1. **A:** remove every all-zero row.
2. **Intermediate:** the compacted sequence of all nonempty rows.
3. **B:** recolor to 9 every nonzero cell that has a nonzero cell immediately
   above or below in the compacted grid.

The source grammar separates all nonempty rows by at least one blank row, so
those vertical contacts do not exist before A. The retained `skip_compression`
counterfactual runs B on the source grid and therefore changes the final result.
The adapter supports two through six demonstrations and one through four
prefix-stable queries. Query four is a substantive 30x30 source with six dense
active rows and boundary contacts. Public turn zero contains demonstrations and
one input-only query; later turns contain only the current input-only query.

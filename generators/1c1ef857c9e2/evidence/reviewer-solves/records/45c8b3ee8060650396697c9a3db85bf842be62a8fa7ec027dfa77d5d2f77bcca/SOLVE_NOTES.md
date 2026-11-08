# Blind-lane solve work log

This is a concise authored work log, not a captured token-level model trace.
No generator, reference program, canonical answers, notes, private query labels,
or previous solution explanation was opened before this solve.

## Exposure qualification

The official `python3 review.py blind prepare` output printed the visible grids
and a summary whose generation_provenance.lesson_check.rivals contained named
hypotheses: fill_with_separator_color, omit_plus_one,
rows_control_both_dimensions, and transpose_row_column_counts. Those names are
rule-adjacent hints. This record therefore uses earlier exposure `unknown`
rather than claiming a completely uncontaminated blind observation. No reference
was deliberately consulted. The tool should hide those fields during solving.

## Revision 1

Visible facts: example 0 has Input: 11 rows × 11 columns. Output: 3 rows × 2 columns;
example 1 has Input: 15 rows × 15 columns. Output: 3 rows × 4 columns;
example 2 has Input: 22 rows × 22 columns. Output: 3 rows × 5 columns.
Each output consists entirely of the non-separator color. There are two full
separator rows in every demonstration. The numbers of full separator columns
are 1, 3, and 4. Adjacent separator columns in examples 1 and 2 count separately,
so counting contiguous separator bands would not fit the displayed outputs.

Candidate rule: output dimensions are full separator row count plus one by
full separator column count plus one; fill with the other color. Identify the
separator by its monochromatic full rows/columns, not by numeric color order.
This also avoids assuming the more frequent color always has the same role.

Check: official blind check with intent solve. No intentional wrong revision or
diagnostic negative was manufactured. The masked query outputs remain unknown.

# Solve notes

All three outputs have one fewer row than their inputs, identifying row 0 as a
column-selection header.  In each example, the output width equals the number
of blue (`1`) header cells, and each output row is exactly the corresponding
body row projected onto those columns in left-to-right order.

The colored decoys make nearby alternatives directly testable.  In example 1,
header color `3` occurs three times while blue occurs twice, yet only the two
blue columns survive.  Therefore neither “most frequent nonzero color,” “all
repeated nonzero colors,” “all nonzero columns,” nor “all odd header values”
explains the labels.  Examples 2 and 3 agree with the same literal-blue mask.

Revision 1 implements that projection without mutating the input.  Earlier rule
exposure is unavoidable from the preceding generator review and is declared;
no rule source, reference solution, previous solve explanation, or private label
was consulted during this solve phase.

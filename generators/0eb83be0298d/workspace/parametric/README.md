# Native template match-count relay prototype

`mode=canonical` is the exact selected wildcard-template rule. In
`mode=match_count_relay`, step A finds all original-orientation wildcard matches;
the intermediate is their count (1–3); step B uses that count to select one of
three color-6 relay anchors and marks it in addition to the canonical corners.
Inputs are independent of the mode.

The adapter supports 2–6 demonstrations and 1–4 queries. With four queries, the
fourth input is exactly 30×30 and uses a 30×26 board. `verify.py` checks matched
inputs, count boundaries and a finite set of template-free, fixed-index and
literal-zero shortcuts. The protected counterfactual derives the relay index
from literal-zero matches instead of wildcard matches.

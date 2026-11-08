# Native parametric family: ruler-selected endpoint threshold

`selection_mode=all_vertical` is the exact 232-byte canonical program and marks
the endpoints of every vertical color-2 component of length at least two.

`selection_mode=ruler_threshold` adds a real sequential dependency. Step A finds
the unique vertical color-7 ruler and measures its input-dependent length. Step B
uses that measured length as the minimum qualifying length for vertical color-2
components, then marks only those components' endpoints. Every scene includes
red lengths below, equal to and above the ruler, plus nonvertical red controls.

The adapter supports 2–6 demonstrations and exactly four private queries. Inputs
are matched across settings; the fourth query is a substantive 30x30 case.

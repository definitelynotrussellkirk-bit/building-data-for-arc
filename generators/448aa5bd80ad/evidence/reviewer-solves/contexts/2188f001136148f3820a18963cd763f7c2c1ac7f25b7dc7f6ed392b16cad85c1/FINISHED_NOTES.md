# Solve work log

Earlier exposure before this blind solve: none. I had not opened task 448aa5bd80ad's generator, rule, notes, solutions, or audit records. I used only `solve-blind/challenge.json` and local reasoning.

## Revision 1 — marker projection count selects the orientation

I first isolated the nonzero, non-9 component and compared its tight crop with each visible output. The three outputs are exact dihedral transforms of that crop:

- example 1 is the transpose;
- example 2 is a left-right mirror;
- example 3 is a 180-degree rotation.

The instruction that distinguishes them is the number of maroon (`9`) marker columns that fall inside the colored object's horizontal bounding interval. The counts are respectively 1, 0, and 2. This gives a single rule that uses the visible marker/object geometry rather than memorizing full marker strings: 0 projected markers → horizontal mirror; 1 → transpose; 2 → rotate 180 degrees.

Both query instances have exactly one marker column inside the object's horizontal bounding interval, so the predicted operation is transpose. Remaining uncertainty: the examples do not establish behavior above two projected marker columns, but neither query requires it. I use the two-or-more branch only as a conservative extension of the observed count-2 case.

## Revision 2 — correct the count-0 transform

The visible checker passed 2/3 examples. A direct comparison showed that example 2 was not merely a left-right mirror: its two unequal middle rows also reverse order. The correct transform is a 180-degree rotation, the same operation used in example 3. I therefore removed the unsupported horizontal-mirror branch.

The repaired visible rule is: exactly one marker column projects through the colored object's horizontal bounding interval → transpose; zero or two projected marker columns → rotate 180 degrees. Equivalently on the observed domain, odd projection parity selects transpose and even parity selects a half-turn. Both masked queries have exactly one projected marker, so their predicted transpose operation is unchanged.

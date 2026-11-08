# Post-repair visible-only solve notes

The output keeps every gray (`5`) cell fixed and changes only zero cells. Each
other nonzero color occurs once in the input and expands through its own
orthogonally connected zero region. Zero regions without a colored seed remain
zero. Diagonal contact does not connect regions: the 7×7 example has nearby
zero pockets that remain distinct unless a cardinal path exists.

I implemented a general row-major seed scan followed by 4-neighbor flood fill.
The original seed cell is temporarily restored to zero before flooding so it
joins its own region. The implementation also has a deterministic meaning for
multiple seeds in one region, although no visible example requires that case.

Earlier exposure: yes. I had inspected this assigned generator and its rule as
part of the required repair before this separate solve. During this solve I used
only the prepared visible examples and did not reopen the generator, canonical
rule, reference solutions, private labels, or earlier solution explanations.

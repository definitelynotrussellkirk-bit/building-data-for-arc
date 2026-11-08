# Forward/reverse normalized stencil family

The default `forward` program is byte-for-byte the selected canonical rule. It
normalizes the first two panel objects, computes the cells present only in the
second object, and paints that input-dependent stencil into the query object.
The `reverse` setting swaps the source panels and therefore transfers the cells
present only in the first object. Inputs are matched across settings.

Each lesson uses 2–6 demonstrations and stores four distinct private queries.
The controller reveals one query at a time. The largest profile is 30×29 because
three equal panels plus two separators cannot form a 30-column input.

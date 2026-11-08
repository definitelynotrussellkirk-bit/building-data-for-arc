# fa3e0c305476

Find every cyan object. Within that object's bounding box, count the connected regions whose cells are not cyan. Recolor the whole object by that count: 1->blue(1), 2->red(2), 3->green(3), 4->orange(7); any other count leaves the object cyan. Sequential sample indices form a linked lesson: demonstrations cover 0,1,2 then 3,4 then 1,5,6; the next query uses only the already-demonstrated 2,3,4 branches.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.

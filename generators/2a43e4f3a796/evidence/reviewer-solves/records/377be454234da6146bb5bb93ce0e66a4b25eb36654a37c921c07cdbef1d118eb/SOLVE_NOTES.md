# Final-source public solve

Earlier exposure: yes. Before this solve I repaired the generator and read the
reference. During this solve I used only the public four-example challenge,
my own new Python program, and visible check feedback. I did not consult
generator source, reference code, private labels, or older solution code/notes.

The original intermediate-source solve is retained in checks/prior-solve. A
first fresh preparation passed, but old solve files reappeared in the public
directory: this numbered the successful new check 0002 and blocked finish
with FileExistsError. All mixed-directory evidence is preserved under
checks/solve-reprepare-collision. This is a technical replay of that same
final-source episode and same successful candidate, not a new hypothesis or
a manufactured failed solve.

## Candidate and public observations

All four examples retain dimensions and color counts. Nonzero cells keep
their column and relative vertical order while moving to the bottom. Example
0 retains a 5 between its surrounding 4s; example 1 retains seven occupied
cells in its first column; example 3 moves color 5 like other nonzero colors.
Examples 0 and 2 use zero as the empty value even when another color is more
frequent. These visible observations support stable downward compaction of
all nonzero cells in each column.

I implemented a bottom-up scan and a destination pointer for each column.
There are no color exclusions, modal-color selection, or population limits.
No failed candidate was submitted. The prior technical check matched all
4/4 visible examples. I am repeating it through the standard command after
preserving the file collision, so the final finished record has one source
and one public episode. Masked-query correctness remains unknown.

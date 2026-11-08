# Independent verifier development evidence

The first regression suite failed because the tool did not exist (14 failures).
The initial implementation then exposed the direct-layout `scripts` import
problem (13 passes, 1 failure). The explicit-lambda parser/bridge route passed
all 14 tests. Subsequent adversarial tests and independent review exposed:

- Boolean/float public cells accepted through Python equality (two failures).
- An unhashable malformed public path (one failure).
- Duplicate JSON keys concealing hidden query labels (one failure).
- A runtime-identity property incorrectly called as a method (one failure).
- Malformed parameter/role fields, unchecked rule-file drift and unchecked
  episode program binding (four failures).

All red JUnit files are retained. The first reviewed run had 21 passes and one
test failure caused by the diagnostic text not including the documented
`program binding` phrase; the rejected bundle itself was correctly rejected.
After correcting that diagnostic, `verifier-reviewed-final.xml` records
**22 passed, 0 failed/errors/skipped**, in 6.58 seconds.

The actual live bundle command is separately retained in
`parametric-verification.json`: 36 setting/input executions, no wrong labels,
no production ambiguities and no rotation ambiguities. Its manifest binds the
intermediate generator `bbefdd3a...`; a later source-bound rerun must be cited
for the final generator. Structural-only receipts never claim Racket execution.

The earlier test output filenames are historical iterations, not claims that
their then-current source is the final handoff. The final task-test and fresh
replay receipts supersede those source bindings without deleting the failures.

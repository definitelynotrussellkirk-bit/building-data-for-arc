# F1: Biggest avoidable friction: public-creation IDs rejected by the test wrapper

Both `review.py task-tests` commands fail with `Unknown puzzle` before collecting the new
task-local tests, although public-creation preflight and direct pytest work. Route declared
public-creation assignments directly to their home tests without requiring catalog registration;
keep owner qualification and approval separate.

# F2: Make export and witness boundary contracts reusable

A locally valid export initially hashed different bytes than it saved, and a valid protected
runtime identity failed the witness header's exact-schema check. Provide a public save-and-hash
helper and a minimal causal-witness constructor that invoke the existing strict validators
before costly preflight; task-local regression-tested versions now ship in this return.

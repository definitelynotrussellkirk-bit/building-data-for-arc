# Exact count-and-pack policies with two sampler banks

The native parameter `secondary` is an episode-fixed policy selector. The two
previously accepted identities and their Racket bytes remain unchanged:

| Value | Exact rule |
| --- | --- |
| `next_repeated` (default) | Exact canonical program; pack the largest mass and largest remaining repeated mass. |
| `big_side_relay` | Derive the largest mass's square side, then select a remaining mass of that count. The exact existing program packs only the largest mass if no such mass exists. |
| `preserve_vertical` | Incoming exact program; pack canonical masses, then rotate 180 degrees unless the largest mass's bounding-box center is strictly above the secondary mass's center. Ties take the rotate branch. |

This is a union of three existing programs, with no Cartesian combination or
rewritten Racket. `family.py` and its programs retain the original relay sampler
and 2–6-demo authoring interface byte-for-byte. `branches/incoming/` retains the
independent incoming source, original `placement` interface and reviewer-reported
evidence. Its canonical bytes equal the selected canonical program. Retention of
that branch and its original manifest does not separately approve its source or
upgrade its reported evidence.

The union adapter supports **3–6 demos and 1–4 queries independently**. Seed
`2*s` selects the relay query bank at original source seed `s`; seed `2*s+1`
selects the vertical query bank at original source seed `s`. Every query is an
exact original sampler draw, including each bank's substantive 30×30 fourth
query. The bank choice never depends on policy. A common, query-blind lesson
uses the original first two relay demos and original third vertical demo.
Optional demos rotate through the other original bank profiles, preserving every
profile across source seeds. All three policies see identical inputs; shorter
requests have identical demo/query prefixes. The three-demo minimum replaces the
old native two-demo minimum because both relay selection and vertical orientation
must be taught, including a contrary horizontal relationship.

The relay policy's no-match branch and the vertical rule's tied-center branch
are explicit consequences of their retained exact programs. The incoming
sampler alone originally required unequal centers; the union retains the full
relay bank, including ties. Python claims follow those exact Racket branches.

Both sequential intermediates remain meaningful: `big_side_relay` computes the
largest side before selecting the secondary count; `preserve_vertical` computes
relative vertical centers before orienting the packed output. Task-local
reconciliation evidence contains protected-Racket contrasts for substituting
side 4 for 9 and forcing `big_above=true` for a below case.

`union_family.public_turn` exposes all demos and exactly one unlabeled query.
Settings, bank/source metadata, programs, answers, and future queries stay
private. Focused evidence is finite; it does not claim universal uniqueness,
learning benefit, training admission, or native acceptance of these new bytes.

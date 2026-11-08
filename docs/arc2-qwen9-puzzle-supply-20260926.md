# Puzzle supply for the ARC-AGI-2 Qwen9 campaign

**Planning/selection note, September 26, 2026.** The two-episode producer and
consumer smoke and 224 verified-family episodes have been exercised. The
68-family explicit-ID quota remains a plan, not a launched batch.

**Historical source snapshot.** Counts and source-bound inventories below were
measured on September 26; subsequent generator integrations can invalidate
their recorded hashes. Rebuild the relevant inventory before another selection. For current
work leads and review commands, use [teammate pickup](onboarding.md) and the
[review guide](../REVIEW/README.md).

HQ's campaign map selects all 1,120
original public tasks as the learner pool. This repository supplies new grid
instances and verified labels; ARC2train
owns rollout captures and learner admission.

## Available producer surface

`arcpuzzles list --approved --count` currently reports **449** effectively
approved generators out of **3,941**. Approved source filters report 219
`training`, 225 `bank` and five `custom`; source tags can overlap (notably
`augmented`), so do not sum arbitrary source-filter counts as disjoint pools.
The [official lineage map](../shared/data/derived/official_generator_lineage.jsonl)
has 1,005 rows, with 964 verified and 41 candidate mappings. Treat candidate
and absent lineage as unresolved, not as independent families.

A [versioned approved-lineage inventory](../var/derived/arc2-approved-lineage-inventory-20260926-v1/manifest.json)
audits every one of the 449 approved generator source hashes and groups them by
disjoint base source class:

| Base source | Approved | Verified original family | Unresolved |
| --- | ---: | ---: | ---: |
| Training | 219 | 218 | 1 |
| Bank | 225 | 0 | 225 |
| Custom | 5 | 0 | 5 |

The 218 verified rows map to **218 distinct original training families**.
Among unresolved rows, 230 have no unambiguous official mapping and one has a
nonverified candidate mapping. `bank` and `custom` are source tags, not proof of
novel rules: their 230 rows need source/semantic overlap review before any
family-reserved holdout assignment. The inventory's 449 per-generator rows,
source file hashes and source-map hashes are retained in `var/derived/`, not
copied into HQ.

The full catalog separates into **1,000 training**, **2,859 bank**, **30
custom**, and **52 entries with no source tag**. The 461 `augmented` tags all
occur alongside `training`, so they do not add a disjoint class. Effective
approval leaves 781 training, 2,634 bank, 25 custom, and 52 untagged entries
unapproved. These counts come from the current `Catalog.query()` source and
approval fields; they describe work to review, not additional usable episodes
or independent ARC rules. In particular, the large bank backlog cannot be
treated as a clean holdout without semantic and source-overlap review.

The 52 untagged entries consist of **49 generic generators** and three
per-puzzle generators; all 52 are effectively unapproved. None of the generic
entries has a canonical rule row. Two carry a raw `reviewed_safe` label but
still fail effective approval because no canonical rule is available. Of the
three per-puzzle entries, `c52e8a19b7d4` and `f0f7628dd21b` are candidate
links to original training tasks, while `7c7796f15a18` has no official
lineage link in the current map. Generic emitted-program tasks may be explored
with explicit unapproved research opt-in, but they are not verified original
variants, approved exports, or independent-family holdouts. They need their
own rule/source review before learner admission.

### Review queue behind the approved pool

A separate [source-bound review inventory](../var/derived/verified-unapproved-official-generator-review-20260926-v1/receipt.json)
(receipt SHA-256 `c4357e065536e12cde78901db2b4162ca7bbea72b64d8355e47e007c0de7bff3`)
joins all 964 verified original-task generator links to current catalog approval
and generator bytes. The 218 approved links above leave **746 current-hash,
lineage-verified but unapproved generators** covering **744 original families**:
744 per-puzzle training generators and two generic generators for one public
evaluation family. Their `rows.jsonl` records every generator ID, family,
source hash, safety label and current approval reasons.
`arcpuzzles list --not-approved --source training --count` returns 781, so that broad filter
also includes 37 training generators outside this verified-link queue.

These 746 are a **review and improvement opportunity**, not 746 usable exports.
Their current safety labels are 277 `provisionally_safe`, 31
`reviewed_standard`, 97 `unverified`, 338 `unsafe`, one `reviewed_unsafe` and
two `unreviewed`; all 746 lack the required current `reviewed_safe` approval.
Additional approval blockers overlap: 25 changed generator hashes, 13 changed
rule hashes, 11 nonpositive mix weights, two missing reviewed generator hashes
and two missing canonical rules. Review work must repair real issues and
refresh source-bound evidence; flipping an approval label does not establish
generator quality. At this snapshot, ZIP return intake and integration were
still pending. They are now implemented; follow the [review guide](../REVIEW/README.md)
and the later [September 29 intake](../REVIEW/intake-20260929-batch11.md).
For triage, **710/746** have only the `not_reviewed_safe` approval reason;
**277** of those carry the weaker `provisionally_safe` label. The other **36**
have at least one additional source, rule, or mix blocker. This suggests a
bounded first review tranche among the 277, with semantic checks and source
evidence still required; it is not a mechanical label-upgrade queue.

The [all-original coverage map](../var/derived/original-generator-coverage-20260926-v1/receipt.json)
(receipt SHA-256 `fe8e5dfa3136aa19195ae321ccd7d657888ec34545a8ac31a03c1008b80e066d`)
joins the pinned all-public 1,120-task source to every current-hash lineage
link. Among 1,000 original training tasks, **218** have an approved verified
generator, **743** have only unapproved verified generators, and **39** have
candidate links only (41 links). Among 120 original public-evaluation tasks,
**one** has two verified but unapproved generic generators and **119** have no
link in the lineage map. Thus 962/1,120 original families have a verified
generator link, but only 218 currently have approved variants. The per-task
`rows.jsonl` distinguishes all four states without exposing query answers.
The 39 candidate-only training families need lineage review; the 119 no-link
evaluation families need new generator work or another validated source before
they can gain generated variants. Neither status affects availability of the
original provided examples themselves.

A [bounded Racket example-fit screen](../var/derived/candidate-original-rule-fit-20260926-v1/receipt.json)
(receipt SHA-256 `bbdefdcb0e3d373030d510af66e52476dcfa238657e2baceb6dc038da4540f5e`)
ran each of the **41 candidate canonical rules** against the corresponding
original task's provided training pairs and private query pairs. **40/41 rules
were exact on every provided pair**, covering **38/39 original tasks**. The
other rule, generator `deb310c21d0c` for task `b74ca5d1`, raised a Racket
runtime error on its first original training input. Its source hash, failure
code and phase are retained without copying private grids into the receipt.
Only one example-compatible candidate, `d6607fc42bcc` for `444801d8`, is
currently generator-approved; the other 39 exact links still have unapproved
generators. Exact fit on these finite examples narrows semantic review but
does **not** upgrade any candidate lineage, prove generated-case parity, or
admit its output to training. Prioritize the approved candidate's lineage
review and the failed rule's repair before using this queue for exports.

For a Qwen9 Pi program-discovery export, choose approved generator IDs and
freeze the selected pool before drawing. The following is a **recipe**, not a
launched batch:

```bash
arcpuzzles list --approved --source training --format ids
arcpuzzles export --approved --source training --count 20 --seed 20260926 \
  --sampling uniform --train 4 --test 9 --draw-difficulty medium \
  --max-attempts 40 --timeout 20 --out var/datasets/arc2-qwen9-demo20
arcpuzzles inspect-export var/datasets/arc2-qwen9-demo20
```

The nine test pairs permit one model-visible masked query and eight distinct
controller-only hidden checks in ARC2kaggle's current generated-task adapter;
the adapter may reject a draw whose inputs repeat. Record those rejections and
the `complete` manifest status. `--count` is accepted episodes, not number of
families; repeated draws can share a rule. A future large export should use an
explicit `--id` pool and family quotas rather than relying on weighted default
sampling. Set a new output path for every run and preserve its manifest, draw
log, rejected examples and source hashes.

The September 26 **two-episode smoke** used this recipe with `--count 2`,
`--max-attempts 8`, and output
`var/datasets/arc2-qwen9-smoke2-20260926/`. It completed two of two draws,
with four visible pairs and nine private-labeled queries per episode, zero
producer rejections, and passed `arcpuzzles inspect-export`. Dataset ID:
`ded8b390a45f3be247431be88145044c35dc157758464747744edab81f2f7590`.
The explicit ARC2kaggle importer accepted both as one masked query plus eight
distinct hidden cases each, with zero importer rejections; its separate staged
artifact is `ARC2kaggle/var/datasets/arc2-qwen9-smoke2-import-20260926/`.
This checks the producer→consumer data path, not a Qwen solve or training
admission. Both imported rows say `family_id: unresolved`: the source catalog
does not populate `family` for these generators even though the separate
official lineage map has verified links from their IDs to original training
tasks `e729b7be` and `d304284e`. Join and verify that sidecar lineage before
any learner admission or family-based split; do not infer a new family from
the missing field.
The join was checked manually for this original smoke: generator `1674812130ff` maps
to `e729b7be` and its current Python source matches the sidecar SHA-256
`f9ec99dc…`; `443eebb271d9` maps to `d304284e` with matching source SHA-256
`3834c7e2…`. Both mappings are marked `verified` and `exact_seed`, so these
draws belong to original training families. The original smoke's unresolved
family fields have not been rewritten.

**New private lineage handoff, implemented and exercised:** generated exports
now write `lineage.private.jsonl`. The producer calls its existing
`Catalog.lineage()` check against the current generator SHA-256; the importer
cross-checks the sidecar, private label, evidence hash, official parent and
family string before assigning the controller-only `family_id`. Unverified
mappings remain unresolved. The new two-family export is
`var/datasets/arc2-qwen9-lineage-two-families-20260926/`, dataset ID
`7143e5630bc7f837224c38a5a452efbe320187423da1253d1c295a77cb0732f1`.
Its independent ARC2kaggle import is
`var/datasets/arc2-qwen9-lineage-two-families-import-20260926/`: two accepted,
zero rejected, with one masked query and eight distinct private checks each.
The imported families are `official:training:d304284e` and
`official:training:e729b7be`; the actor projection contained neither family
nor answer. The producer suite passed 58 tests and the consumer suite passed
200, with 57 skipped. This is lineage and data-flow evidence, not a model solve
or learner admission. The private sidecar is bound to the export manifest;
ARC2train must still recheck source/admission gates before using a route for
training.

**Verified-family pool draw, exercised September 26:** an explicit pool of all
218 approved generators with hash-verified official training-family lineage
was sampled uniformly at seed `20260926`, medium difficulty, four visible
pairs and nine query pairs. The completed versioned export is
`var/datasets/arc2-qwen9-verified-family-pool40-20260926-v2/`, dataset ID
`59aefcedfde17894704707eb80598e3e12f313c8b11d98bce5a30b1b00f1c91a`.
It produced **40/40 accepted episodes from 35 distinct original training
families**, with ten individual duplicate-pair rejections retained inside
otherwise accepted draws. `inspect-export` passed; all 40 lineage sidecar rows
are verified. The separate ARC2kaggle import at
`ARC2kaggle/var/datasets/arc2-qwen9-verified-family-pool40-import-20260926-v1/` accepted
all 40, with one masked query and eight distinct private checks per episode,
zero importer rejections and `training_eligible=false` throughout. This is
usable within-family puzzle supply, not 35 new independent ARC rules.

The first output directory with suffix `-v1` is deliberately retained as an
incomplete failure: its launch environment omitted `PATH`, so the Racket
runtime was unavailable and all 80 draws were rejected. Version `-v2` used
the normal environment and completed; the failed artifact is not included in
the yield figure.

A second uniform draw excluded the first 35 families and sampled the remaining
183 verified generators at seed `20260927`, requesting 183 episodes. Export
`var/datasets/arc2-qwen9-remaining183-draw183-20260926-v1/`, dataset ID
`fe018b55d63ec2e93fe5daead5853ed198cb93990a4b52d4ffac9bb9d48b1979`,
completed **183/183** from **114 additional original training families**.
Its verifier passed; it retained 30 rejected duplicate pairs and one rejected
identity-output pair inside accepted draws. ARC2kaggle's separate
`arc2-qwen9-remaining183-draw183-import-20260926-v1` accepted all 183, zero
importer rejections, each with one masked query and eight distinct private
checks. Combined with the first bundle, the measured supply is **223 episodes
across 149 distinct verified families**. The other **69** verified generators
are not yet represented by an accepted episode; draw them by explicit ID or
per-family quota rather than assuming another with-replacement batch will cover
them. None of these 149 families is a new independent rule or a clean holdout.
The exact remaining IDs, generator hashes and source-export bindings are in
`var/derived/arc2-qwen9-remaining-verified-families-20260926-v1/` (69 rows,
rows SHA-256 `656ffa3d95ae6e5486b390ce999a40f24f77a4144d1835bf02d21f2a4b2cb735`).
One explicit-ID follow-up tested the quota route: generator `a9f315ca9cc7`
(`official:training:007bbfb7`) produced one accepted 4+9 episode at seed
`20260928`; `inspect-export` and the ARC2kaggle importer both accepted it with
verified lineage and zero importer rejections. The cumulative local supply is
**224 episodes from 150 verified original training families**. A new immutable
`var/derived/arc2-qwen9-remaining-verified-families-20260926-v2/` list binds
the predecessor and this targeted export and contains the **68** still absent
families. This tests one explicit-ID draw, not all 68 generators' yield.

## Completing the verified-family coverage

The remaining-family inventory binds **68 distinct, hash-verified training
generators to 68 different original training families**. All 68 current
`generators/<id>/generator.py` bytes matched the inventory's recorded SHA-256
values at this audit. The export command's
repeated `--id` option creates a sampling pool, but `--sampling uniform` still
draws **with replacement**. A 68-draw pool export therefore cannot guarantee
one accepted episode per missing family. The coverage route is one bounded,
versioned export per generator ID (or a future explicit quota sampler), with
each resulting manifest and rejected draw retained. Check the current source
hash against `rows.jsonl` before every draw; `inspect-export` and the private
lineage sidecar must pass before handing an episode to ARC2kaggle. Count only
accepted episodes and distinct verified families, not requested draws.

Generation and Racket reference checks are CPU work. The completed Qwen9
Spark allocation has been released; a generator batch does not need to reserve
its GPU/RAM pool. Run the generator quota on a pinned local environment or the
LAN `cpu` partition. No 68-family quota batch or dedicated Spark generator job
has been launched.

The [frozen 68-job quota plan](../var/derived/arc2-qwen9-remaining-family-export-plan-20260926-v2/manifest.json)
(manifest SHA-256 `07a70f488595bdeeab4c748a7637a23cd9a089ba08cbe4d819b8a152c57bb951`)
now records one explicit generator ID, expected original family, current
generator hash, distinct seed, bounded 4+9 export command and unique output
path per missing family. It is a launch-ready plan, **not 68 generated
episodes**. The plan leaves failed or partial exports intact and requires an
`inspect-export` and lineage check before each resulting episode can join a
consumer bundle.
Its preserved v1 predecessor assumed `arcpuzzles` was on `PATH`; the v2
commands invoke the pinned `.venv/bin/python -m arcpuzzles` explicitly. Neither
version has been launched.
ARC2train's source-hashed priority overlay (local artifact
`ARC2train/var/derived/generated-family-quota-priority/2026-09-26-v1/manifest.json`)
matches all 68 frozen jobs by original family, generator ID and source hash.
It puts the 41 families without a strict-good Qwen9 route on their original
task in a first planning group, with the other 27 second. The original jobs,
seeds and output paths are unchanged; original-task status is not a Qwen9
measurement on generated instances.

Only `public.jsonl` enters the actor workspace. Keep `labels.private.jsonl`,
`lineage.private.jsonl`, `episodes.private.jsonl`, reference programs and source provenance behind the
trusted scorer. An approved generator and a complete export still require
family/split admission checks in ARC2train. Derived program mutations and
unapproved generators remain separate research data.

## Internal holdout boundary

Because the learner pool includes every original public task, a generated
variant with verified lineage to one of those tasks is **not** an unseen-family
holdout. Use those variants for within-family practice or robustness only.
For an internal family holdout, first audit bank/custom or newly reviewed
generators for original-task and semantic overlap; then freeze whole selected
families, including every seed/difficulty, outside learner and teacher training.
Unknown lineage cannot be promoted to a clean holdout by assigning a random
split. The Kaggle competition score remains the external outcome check.

A read-only catalog grouping check on `catalog/puzzles.jsonl` SHA-256
`f92946ab931cafb61ca094fa8c79ee9f8478fbc771b2586e1ec1424bfd09707c`
found that all **230** effectively approved bank/custom generators lack populated
`family` and `split` fields. The **225 bank generators** map to **107 distinct**
`bank:<id>` source tags; each bank generator has exactly one such tag, and
some tags cover multiple variants. The five approved custom generators carry
only the generic `custom` tag. A provisional bank holdout must therefore keep
every generator sharing a `bank:<id>` tag on the same side of the split, and
custom entries need individual provenance review before grouping. This source
grouping is only a minimum separation rule, not proof that any group is
semantically independent of the 1,120 originals or another bank group.

A first exact-overlap screen is retained in
`var/derived/approved-bank-custom-exact-overlap-20260926-v1/receipt.json`.
It compared 937 canonical input/output pairs from all 225 approved bank and
five approved custom generators with 4,838 provided and original-query pairs
from the 1,120 public tasks. It found zero exact pair matches, zero identical
selected rule hashes against approved training generators, and no declared
parent IDs. This rules out those exact-match signals only; the 230 generators
still need semantic/source review before any is called a new family or reserved
as a holdout.

A broader [rule-source screen](../var/derived/approved-bank-official-rule-screen-20260926-v1/receipt.json)
(SHA-256 `46a8dd12f2fd98fed4d0d6c897caa5d94f3bda414a8e2baca30a2bc86e5eea63`)
compared those 230 approved bank/custom rules with all **964 verified official
generator links** (962 training, two public evaluation), including unapproved
original-task generators. It found zero whitespace-normalized identical rule
sources and one direct-unary syntax candidate: bank `E37` versus training task
`74dd1130`, the transpose overlap confirmed below. Two generic official links
had no selected canonical Racket rule and were excluded from rule comparisons.
The other public tasks without a verified generator link are outside this
rule-source screen. Rule-source dissimilarity does not establish semantic
independence.

A follow-up [source-bound semantic-overlap receipt](../var/derived/approved-bank-training-semantic-overlap-20260926-v1/receipt.json)
(SHA-256 `9f46a8932faec62c4001d6cb255f75afc3afe0cc5f3a8a6893296b7c203cb492`)
identifies one real overlap missed by the exact screen. Approved bank generator
`c86f5a19e34d` (`E37`) and original-training generator `19a48004b265`
(`official:training:74dd1130`, currently unapproved) both implement transpose. Their selected
Racket rules differ as text, but each rule passed all canonical pairs of both
tasks in the isolated Racket verifier, including each task's query pair: four
program/task checks passed. The bank item is therefore a known correlated
variant, not an independent family holdout. This finding classifies that one
item only; it does not resolve the other bank/custom lineage questions or
change their catalog labels.
The same `bank:9f3a2c87618d` source tag also contains approved generators
`947a1d9ca8f5` and `e9238d278276`. Their rules are not classified by the
transpose check, but the shared source grouping above means all three must be
kept out of a reserved unseen-family holdout until that source group's
provenance is resolved.

A separate [targeted Racket cross-execution](../var/derived/approved-bank-original-related-rule-20260926-v1/receipt.json)
(SHA-256 `a17f27f69c40dcd931e6cc7a6dc5632316368aa6e1c98a8b2b6f00b2f6d6b17c`)
of approved bank `3ab6810fc781` and
original-training generator `5dedfc297cf5` found one-way coverage: the bank
rule passed the original generator's canonical train/query examples, while the
original rule failed on the bank's train examples. Their descriptions distinguish
largest nonzero component from largest same-color object. This is a related-rule
review candidate, **not** a proven duplicate or independent-family admission.

Pair reorders and leave-one-out demonstrations from original public tasks are
views of their parent, not generator episodes. Their actor-facing projection
must keep query answers private, preserve the canonical task ID and record the
exact view/order. DPO comparisons require the same initial view and prefix on
both routes; pass@2 evaluation fixes both views before looking at private
scores. The ARC2train panel
owns the original task/view inventory.

# ARCpuzzles repository rules

Read README.md and the relevant guide in docs/. User instructions take precedence.
Work directly unless the user explicitly requests delegation.

- Older inactive experiments and historical launchers remain in ARCagi2 until
  the user explicitly asks to import them. See docs/deferred-imports.md.

- Own puzzles, generators, reference rules, generation, validation, and exports.
  Optimizers, model checkpoints, inference policies, and competition submission
  code belong elsewhere. Interactive game implementations belong in ARCgames.
- Check Git status before editing. Preserve predecessor checkouts; copy source
  and evidence during extraction, never move or delete user work.
- Each checkout must be independently usable. No sibling/predecessor imports,
  symlinks, editable dependencies on other worktrees, or borrowed environments.
  Declare third-party dependencies and document required runtime executables.
- Follow docs/placement.md. Retain puzzle IDs, generator seeds, family/split
  lineage, rules, associated notes, and review evidence together.
- Keep current generator decisions and reversals in its notes.md; keep minimal
  counterexamples and source-bound audits in that generator's home. Common tool
  requests live in REVIEW/suggestions.json as one current row per request.
  Owner direction October 7: no cumulative historical review ledger. After triage,
  retain current notes/decisions, actionable source-bound audits/reproductions,
  exact-source approval and useful authored solve data; compact verified processed
  returns and remove managed ZIPs/expansions. Raw archives are temporary intake,
  not permanent retention. Explicitly resolve or reopen audits;
  source changes and generic acceptance do not clear audit_unresolved. Follow the
  placement guide's extraction/disposal gate before deleting reviewer archives.
- Reference rules remain Racket where that is their existing contract. Derive
  labels through the reference runtime. Preserve review/admission distinctions;
  a successful import or smoke run does not upgrade a safety label.
- Reviewer returns use the owner's October 3 lightweight acceptance policy:
  spend about one minute per ordinary ZIP, up to ten for a substantial upgrade.
  Read the short repair summary and general feedback; blanket accept routine
  improvements using `review integrate --reviewer-reported`. Inspect further
  only for a concrete conflict or larger design change. Do not routinely rerun
  batteries, every task test, private solves, or read every historical note.
  Preserve hashes, notes and reviewer evidence; label unrerun results as
  reviewer-reported. Owner clarified October 3: an accepted generator repair
  IS its safety review. Full-packet integration automatically marks that exact
  source/rule reviewed_safe and approved; backfill with `review approve
  --all-integrated`. Preserve reported failures/limits and random adversarial
  findings. Superseded code cannot approve new bytes; active semantic vetoes
  remain. Generator approval does not admit model trajectories to training.
  The old global intake skill was deleted; do not recreate or invoke it.
- Owner direction October 24: routine reviewer-ZIP refreshes use
  `review pack-full --fast`, with the bundled Racket archive, and atomically
  replace `var/review/SEND-THIS-ARCpuzzles-review.zip` immediately. Do not block
  delivery on intake backlog, historical evidence graphs or cold validation.
  Publish assignment/workflow step changes first, then resume intake. A pause
  requested only for publication ends when the sendable ZIP is ready.
  Record deep validation as pending and run it separately when time permits or
  changes warrant it. Generator qualification/acceptance gates are unchanged.
- Transfer data through versioned, content-hashed bundles. Keep answers and
  reference programs separate from model-visible evaluation challenges.
- Extraction verification must exercise generation and reference execution from
  a relocated checkout with no predecessor/sibling source on its import path.
- Source snapshots and inherited receipts are provenance, not executable
  dependencies or proof that the new checkout passed those checks.
- Put generated datasets, caches, and temporary output in ignored var/ or build/.
  Document explicit artifact retrieval; never commit credentials or weights.
- Report what is implemented, what was actually exercised, and what remains.

- Do not create per-batch narrative intake/transport summaries (for example
  `docs/reviewer-solves-YYYYMMDD-batchNN.md`). Use existing machine receipts,
  manifests and task records for counts/hashes. Keep actual reviewer feedback,
  audits, decisions and workspaces with their task. Update one existing pickup
  page only when the next action or workflow changes; routine intake needs no
  new prose document, dated status section or matching HQ summary.

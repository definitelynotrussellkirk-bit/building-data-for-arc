#!/usr/bin/env python3
"""Replay the assignment's bounded allocation audit, reading selected ZIP members only.

This report generator performs 21 tiny input-generator calls (20 grids, one
intentional rejection), no Racket execution, no dataset export, no mutable draw,
no production edits, and no blind-solve/private-label access. The narrative is
specific to the pinned packet; its manifest hash and source hashes are checked.
"""
from __future__ import annotations
import argparse
import ast
import collections
import hashlib
import json
from pathlib import Path
import random
import sys
import types
import zipfile

AUDIT_SEED = '77e4493c00addcfebbc4cc99cafd86e44a9be839938cf6b19e918d43c4cde85e'
EXPECTED_IDS = ['b6edfc119780', '10bc62b2de84', '69ebef53a2ac']
PACKET_SHA256 = 'd6455f690c4ca33908aed3eada89e50d2dcac36352ad1bdde82b0f0f3d70cf12'
BASE = 'WORK/repo/'
AUTHORITY_PATHS = {
    'b6edfc119780': 'shared/data/base/solutions/banks/129d068bbf4e/S18_E7__b6edfc119780.json',
    '10bc62b2de84': 'shared/data/base/solutions/banks/5dfff1627b31/medium_p06__10bc62b2de84.json',
    '69ebef53a2ac': 'shared/data/base/solutions/banks/2eea055c3155/easy_04__69ebef53a2ac.json',
}
PROPOSAL = 'shared/tools/proposals/807e705cf509db23/'
RETAINED_LOG = PROPOSAL + 'checks/semantic-first/checks/10bc62b2de84_after_semantic_gate.log'
APPROVAL = 'REVIEW/approvals/72e86a2a95e965799c56ab6264dddc5b05cdb34397b8945b4dc42e790a86d914.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_sha(value):
    return sha(json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode())


def load_module(z, name, path):
    module = types.ModuleType(name)
    module.__file__ = path
    sys.modules[name] = module
    exec(compile(z.read(path), path, 'exec'), module.__dict__)
    return module


def bounded_probes(z):
    for name in ('puzzle_generators', 'puzzle_generators.helpers'):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    load_module(z, 'puzzle_generators.base', BASE + 'shared/runtime/puzzle_generators/base.py')
    load_module(z, 'puzzle_generators.helpers.grid', BASE + 'shared/runtime/puzzle_generators/helpers/grid.py')
    modules = {gid: load_module(z, 'allocation_audit_' + gid,
               BASE + f'generators/{gid}/generator.py') for gid in EXPECTED_IDS}
    mirror = modules['69ebef53a2ac']
    baseline = None
    mirror_calls = []
    for label, overrides in [
        ('baseline', {}), ('one_mark', {'num_marks': 1}),
        ('six_marks', {'num_marks': 6}), ('two_colors', {'n_distinct_colors': 2}),
        ('rainbow', {'palette_kind': 'rainbow'}), ('unknown_key', {'mispeled_axis': 1})
    ]:
        grid = mirror.generate(17, 0, **overrides)
        if baseline is None:
            baseline = grid
        mirror_calls.append({
            'case': label, 'seed': 17, 'sample_index': 0, 'overrides': overrides,
            'same_as_baseline': grid == baseline, 'input_sha256': json_sha(grid),
            'nonzero_cells': sum(v != 0 for row in grid for v in row),
            'nonzero_colors': len({v for row in grid for v in row if v}),
            'self_check': mirror.self_check(grid),
        })
    assert all(row['same_as_baseline'] and row['nonzero_cells'] == 4
               and row['nonzero_colors'] == 1 and not row['self_check'] for row in mirror_calls)
    row = modules['b6edfc119780']
    try:
        row.generate(17, 0, num_active_rows=3, winner_rank=2, tie_mode='top_tie')
    except ValueError as exc:
        rejection = {'error_type': 'ValueError', 'message': str(exc)}
    else:
        raise AssertionError('Expected incompatible tie override to reject')
    grids = [row.generate(17, i) for i in range(7)]
    demos = [{'input': grid, 'output': row.rule_mirror(grid)} for grid in grids[:3]]
    row_probe = {
        'seed': 17, 'sample_indices': list(range(7)), 'demonstrations': 3, 'queries': 4,
        'distinct_inputs': len({json_sha(grid) for grid in grids}),
        'input_sha256': [json_sha(grid) for grid in grids],
        'per_query_current_python_hook_reasons': [row.lesson_identifiable(demos, {'input': grid})
                                                   for grid in grids[3:]],
        'labels': 'Python rule_mirror only; no fresh Racket label claim',
        'intentionally_rejected_override': {
            'seed': 17, 'sample_index': 0,
            'overrides': {'num_active_rows': 3, 'winner_rank': 2, 'tie_mode': 'top_tie'},
            **rejection,
        },
    }
    assert row_probe['distinct_inputs'] == 7
    assert row_probe['per_query_current_python_hook_reasons'] == [[], [], [], []]
    pack = modules['10bc62b2de84']
    grids = [pack.generate(17, i) for i in range(7)]
    pack_probe = {
        'seed': 17, 'sample_indices': list(range(7)), 'demonstrations': 3, 'queries': 4,
        'distinct_inputs': len({json_sha(grid) for grid in grids}),
        'input_sha256': [json_sha(grid) for grid in grids],
        'unequal_height_witness': [pack._has_unequal_heights(grid) for grid in grids],
        'self_check': [pack.self_check(grid) for grid in grids],
        'labels': 'No outputs generated; no fresh Racket label claim',
    }
    assert pack_probe['distinct_inputs'] == 7
    assert all(pack_probe['unequal_height_witness']) and not any(pack_probe['self_check'])
    return {'scope': '21 generator calls; 20 returned grids and one intended domain rejection',
            'racket_executions': 0, 'model_jobs': 0,
            '69ebef53a2ac': mirror_calls, 'b6edfc119780': row_probe, '10bc62b2de84': pack_probe}


OBSERVATIONS = {
    'b6edfc119780': {
        'representation': 'Sparse row markers -> inclusive span closure, longest-span selection, stable topmost tie break, cyan paint.',
        'teachability': 'Current 12-slot schedule covers unique maxima/ties, winner rank, color reuse and marker-count counterexamples; current lesson_identifiable implements nine noncanonical rivals.',
        'parameter_coverage': 'Seven input-distribution axes; no task-local parametric-rule workspace in this snapshot. Fixed rule axes are not episode rule parameters.',
        'four_query_coverage': 'No retained Racket-verified four-query receipt in the selected home. Seed-17 3+4 Python-only probe is distinct and passes the current hook; this is not production/Racket certification.',
        'retained_findings': 'Five associated notes report tie handling, explicit incompatible-tie rejection, active-authority agreement, canonical-profile repair and low global density. The density warning is task-dependent and is not evidence that sparse endpoints are poor labels.',
        'evidence_status': 'Associated notes are inherited reports without source SHA bindings. Referenced old checks are not assumed current; current source and focused tests support implementation inspection only. Packet approval remains false/provisionally_safe.',
        'rejected_draws': 'Fresh bounded probe confirms a requested last-row winner plus top_tie rejects instead of silently changing the request. This is a lawful incompatibility, not a defect rate.',
        'grammar_limits': 'Executable target uses filtering, row grouping, interval construction, stable sorting and painting. It does not cover orientation changes, episode rule variants, or arbitrary rival grammar.',
        'repair_cost_estimate': 'Estimate, not timing: 10-30 reviewer minutes to bind existing focused checks and a small four-query Racket receipt; approval can still require other unresolved gates.',
    },
    '10bc62b2de84': {
        'representation': '4-connected objects -> left-edge sort -> bounding-box crops -> one-column gaps -> bottom alignment.',
        'teachability': 'Current generator requires unequal crop heights on every ordinary input, separating top alignment. Finite placement/backtracking replaces earlier silent object loss; validation still accepts lawful equal-height canonical examples.',
        'parameter_coverage': 'Three exact input axes (height, width, object count); no task-local parametric-rule workspace in this snapshot. Shapes/colors/gaps/alignment are not exposed rule parameters.',
        'four_query_coverage': 'Notes report a 300-lesson census and query rotations, which are not four simultaneous queries. Fresh seven-input mechanical probe has no repeats and every input exhibits unequal heights; no fresh Racket labels.',
        'retained_findings': 'Source-bound current approval is reviewer_reported. Notes report 24,480/24,480 override calls, 44 portable tests and all 630 axis combinations. These reported counts were not rerun. Retained semantic-first log warns declared_period_not_enumerated; current source no longer declares LESSON_SCHEDULE_PERIOD, so the warning belongs to an intermediate source, not the current one.',
        'evidence_status': 'Current generator SHA exactly matches catalog, packet, review_index and approval receipt. SUMMARY.md still says imported version 2.0.2 while current source/catalog say 3.0.0; use current code and source-bound review record.',
        'rejected_draws': 'Notes describe baseline requested-six/returned-five placement failure and unknown-key/type rejection after repair. No retained current production rejection-rate ledger was located in the selected home.',
        'grammar_limits': 'A single declared top_aligned rival does not establish universal identifiability. Same-color objects, touching objects and tied left edges are excluded. Raw archival primitive chains include unused helpers, so they do not measure current executable grammar coverage.',
        'repair_cost_estimate': 'Estimate, not timing: 5-15 reviewer minutes for a focused four-query/export receipt using existing witness/rival hooks. Expanding shape count or rule parameters adds unmeasured review and backtracking cost.',
    },
    '69ebef53a2ac': {
        'representation': 'Copy the left half to a horizontal mirror in the right half; ordinary input is one connected, one-color component.',
        'teachability': 'Comments promise a multicolor demonstration to refute color-specific mirroring, but current source enforces one color. A four-demo count is asserted without an executable lesson/rival contract in this file.',
        'parameter_coverage': 'AXES lists nine controls; ordinary generation consumes keyed grid_h/grid_w only. Source samples mark count and color directly from layout RNG. No task-local parametric-rule workspace.',
        'four_query_coverage': 'EXAMPLES_NEEDED=4 describes demonstrations, not query count. No source-bound four-query receipt, duplicate check or per-query rival evidence was located in the selected home.',
        'retained_findings': 'No associated notes, review_index or retained linter receipt in this selected home. RULE_HASH is absent in current source. These are inspected facts; no fresh full linter pass/fail is claimed.',
        'evidence_status': 'Packet approval false, catalog provisionally_safe. Current summary/comment language about varied colors is stale relative to the one-color code path.',
        'rejected_draws': 'Seed 17/index 0 silently accepts num_marks=1 and num_marks=6, n_distinct_colors=2, rainbow and an unknown key; all return the same four-mark, one-color grid and pass self_check. This is one reproducible contract failure, not a corpus rejection-rate estimate.',
        'grammar_limits': 'Fixed horizontal reflection has narrower coverage than declared palette/texture metadata implies; there is no evidence here for multicolor conditional behavior, alternative axes or an episode grammar.',
        'repair_cost_estimate': 'Estimate, not timing: 30-60 reviewer minutes to reconcile dead controls, pin authority and add a lawful rival/witness check. Do not increase this source volume merely because its weight is 1.0.',
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--work-root', type=Path)
    args = ap.parse_args()
    with zipfile.ZipFile(args.archive) as z:
        names = set(z.namelist())
        manifest_raw = z.read('WORK/PACKET-MANIFEST.json')
        assert sha(manifest_raw) == PACKET_SHA256, 'Narrative is pinned to the original packet'
        manifest = json.loads(manifest_raw)
        ids = random.Random(int(AUDIT_SEED, 16)).sample(sorted(manifest['generators']),
                                                       min(3, len(manifest['generators'])))
        assert ids == EXPECTED_IDS
        catalog_raw = z.read(BASE + 'catalog/puzzles.jsonl')
        catalog = [json.loads(line) for line in catalog_raw.decode().splitlines() if line]
        catalog_by_id = {row['id']: row for row in catalog}
        paths = {
            'WORK/PARAMETRIC-RULES.md', BASE + 'catalog/puzzles.jsonl',
            BASE + 'src/arcpuzzles/review_full_draw.py', BASE + 'src/arcpuzzles/datasets.py',
            BASE + 'src/arcpuzzles/catalog.py', BASE + 'shared/runtime/puzzle_generators/base.py',
            BASE + 'shared/runtime/puzzle_generators/helpers/grid.py', BASE + APPROVAL,
            BASE + RETAINED_LOG, BASE + PROPOSAL + 'manifest.json',
            BASE + 'REVIEW/questions/qwen9-data-value.json',
            BASE + 'generators/4ca8a7b38652/workspace/parametric/prototype.py',
            BASE + 'generators/4ca8a7b38652/workspace/parametric/README.md',
        }
        records = []
        pp = manifest['parametric_priority']
        for gid in ids:
            home = BASE + 'generators/' + gid + '/'
            relevant = sorted(n for n in names if n.startswith(home)
                              and '/reviewer-solves/' not in n and not n.endswith('/'))
            paths.update(relevant)
            authority_path = BASE + AUTHORITY_PATHS[gid]
            paths.add(authority_path)
            authority = json.loads(z.read(authority_path))
            source = z.read(home + 'generator.py')
            tree = ast.parse(source)
            assigned = {target.id for node in tree.body if isinstance(node, ast.Assign)
                        for target in node.targets if isinstance(target, ast.Name)}
            functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            historical_links = []
            notes_path = home + 'evidence/associated_notes.jsonl'
            for line in z.read(notes_path).decode().splitlines():
                if not line.strip():
                    continue
                note = json.loads(line)
                for ref in note.get('evidence', []):
                    file_ref = ref.split('::')[0]
                    matches = sorted(n for n in names if n.endswith('/' + file_ref))
                    historical_links.append({'note_key': note['note_key'], 'reference': ref,
                                             'matching_packet_members': matches})
            records.append({
                'id': gid, 'packet_generator': manifest['generators'][gid],
                'catalog': catalog_by_id[gid],
                'source_sha256_matches_manifest': sha(source) == manifest['generators'][gid]['generator_sha256'],
                'source_path': home + 'generator.py', 'evidence_paths_inspected': relevant,
                'authority_path': authority_path,
                'selected_rule_text_sha256': sha(authority['racket_target']['target_code'].encode()),
                'selected_rule_text_chars': len(authority['racket_target']['target_code']),
                'source_bindings': {'RULE_HASH_present': 'RULE_HASH' in assigned,
                                    'LESSON_SCHEDULE_PERIOD_present': 'LESSON_SCHEDULE_PERIOD' in assigned,
                                    'lesson_identifiable_present': 'lesson_identifiable' in functions,
                                    'SEMANTIC_RIVALS_present': 'SEMANTIC_RIVALS' in assigned},
                'pool_membership': {'main': gid in manifest['main_ids'],
                                    'normal': gid in manifest['main_draw_policy']['normal_ids'],
                                    'tiers': [key for key, pool in pp['tiers'].items() if gid in pool]},
                'retained_historical_note_links': historical_links,
                'observations': OBSERVATIONS[gid],
            })
        inventory = []
        for path in sorted(paths):
            raw = z.read(path)
            expected = manifest['files'].get(path.removeprefix('WORK/'))
            assert expected == sha(raw), path
            row = {'path': path, 'bytes': len(raw), 'sha256': sha(raw), 'packet_hash_matches': True}
            if args.work_root:
                live = args.work_root / path.removeprefix('WORK/')
                row['live_present'] = live.is_file()
                if live.is_file():
                    row['live_sha256'] = sha(live.read_bytes())
                    row['live_matches_packet'] = row['live_sha256'] == row['sha256']
            inventory.append(row)
        assignment = None
        if args.work_root:
            raw = (args.work_root / 'ASSIGNMENT.json').read_bytes()
            contract = json.loads(raw)
            derived = sha(bytes.fromhex(contract['seed']) + b':allocation-audit')
            assert derived == AUDIT_SEED and contract['packet_id'] == PACKET_SHA256
            assignment = {key: contract.get(key) for key in
                          ['assignment_id', 'task_id', 'seed', 'question', 'authoring_focus']}
            assignment.update({'sha256': sha(raw), 'derived_audit_seed_matches': True})
        focus = manifest['main_draw_policy']['evaluation_focus']
        report = {
            'schema': 'arcpuzzles-bounded-allocation-audit-v1', 'scope': 'Read-only proposal; no policy, approval or admission changes',
            'archive_filename': args.archive.name, 'packet_manifest_sha256': PACKET_SHA256,
            'assignment': assignment, 'audit_seed': AUDIT_SEED,
            'sampling_algorithm': 'random.Random(int(audit_seed, 16)).sample(sorted(manifest["generators"]), min(3, len(manifest["generators"])))',
            'sampled_ids_in_draw_order': ids,
            'policy': {
                'all_generator_count': len(manifest['generators']),
                'manifest_approved_count': sum(bool(row.get('approved')) for row in manifest['generators'].values()),
                'main_ids_count': len(manifest['main_ids']), 'normal_ids_count': len(manifest['main_draw_policy']['normal_ids']),
                'priority_counts_as_reported': pp['counts'], 'priority_tier_sizes': {key: len(value) for key, value in pp['tiers'].items()},
                'selected_tier': pp['selected_tier'], 'provided_tasks': pp['provided_task_count'],
                'covered_original_tasks': pp['covered_original_tasks'], 'unmapped_original_tasks': len(pp['unmapped_original_tasks']),
                'evaluation_focus': {key: value for key, value in focus.items() if key != 'anchors'},
                'evaluation_anchor_tiers': dict(collections.Counter(row['selected_tier'] for row in focus['anchors'])),
                'mapped_evaluation_anchors': [row for row in focus['anchors'] if row['main_ids']],
                'nominal_probability_interpretation': {
                    'public_evaluation_focus': '1/10 authoring assignments, not dataset rows',
                    'direct_related_evaluation_target': '1/10 * 1/120 = 1/1200 of assignments at this snapshot; each of two descendants 1/2400',
                    'normal_target_including_fallback': '1199/1200 total; each of 250 normal targets approximately 1199/300000',
                    'qualification': 'Analytical intended uniform-hash draw probabilities, not measured assignment frequencies; negligible modulo bias is not estimated.'
                },
                'authoring_vs_dataset': 'review_full_draw uses seed/hash modulo selection and no mix_weight. Dataset export defaults to approved=True and then rng.choices with positive mix_weight within the selected filter pool. Approval and trainee-trajectory admission remain separate.',
            },
            'catalog': {
                'rows': len(catalog), 'mix_weight_counts': dict(collections.Counter(str(row.get('mix_weight')) for row in catalog)),
                'train_safety_counts': dict(collections.Counter(row.get('train_safety') for row in catalog)),
                'sample_weights': {gid: catalog_by_id[gid]['mix_weight'] for gid in ids},
                'sample_provenance': {gid: catalog_by_id[gid]['sources'] for gid in ids},
                'sample_representativeness_limit': 'Three uniform record IDs, all bank lineage, are not a stratified sample of the current authoring queue or approved dataset mixture. ARC-GEN and RE-ARC were not sampled; no source-wide ranking or volume recommendation follows.'
            },
            'records': records, 'bounded_current_source_probes': bounded_probes(z),
            'retained_source_receipt': {
                '10bc62b2de84_approval': json.loads(z.read(BASE + APPROVAL)),
                'semantic_first_log_path': BASE + RETAINED_LOG,
                'semantic_first_log_status': 'Historical intermediate-source WARN; do not relabel as current failure or as current-source census proof',
                'lint_limits': 'Current-source full linter results were not located in the three selected generator homes. 10bc notes report final lint green, inherited/reviewer-reported. No new linter execution is claimed. Absence of receipts is not a pass.',
            },
            'alternative_allocation': {
                'proposal': 'Keep the 10% focus and all main-draw probabilities. For a fixed local labeling/review budget, prioritize source-bound control/lesson repairs and trial four distinct queries on an already approved family before adding more same-rule one-query episodes.',
                'comparison_unit': 'Four usable queries with three demonstrations per episode; costs are distinct pair-label evaluations before cache reuse.',
                'baseline_four_one_query_episodes': {'racket_pair_labels': 16, 'candidate_input_hashes': 16, 'queries': 4},
                'alternative_one_four_query_episode': {'racket_pair_labels': 7, 'candidate_input_hashes': 7, 'queries': 4},
                'arithmetic': {'pair_labels_saved': 9, 'fraction_saved': 0.5625, 'query_per_pair_label_ratio': 16/7},
                'estimated_quality_per_cost': 'Conditional estimate: if all four queries are distinct, Racket-correct and demo-identifiable, useful-query yield per pair label is 16/7 (~2.29x). This does not increase rule/grammar diversity by itself or measure Qwen learning benefit. Correlated queries, cached labels, longer prompts, rejection rates and per-family runtime may change the net gain.',
                'review_cost': 'The 5-15 minute packer receipt estimate is below the 30-60 minute mirror-contract repair estimate, but repair has higher value for trustworthy declared coverage. Time estimates are unmeasured and must not be used to promote unapproved data.',
                'bounded_test': 'Propose only: on approved 10bc62b2de84, seeds 17 and 23, materialize two 3-demo/4-query episodes (14 pair labels). Require matching Racket rule hash, input disjointness across all pairs, and every query identifiable from only its three demonstrations against the existing top-aligned rival. Reuse current accepted evidence for other gates; compare against 8 one-query episodes (32 pair labels) only if cached receipts exist.',
                'stopping_rule': 'Cap the pilot at 20 reviewer minutes and 28 pair-label attempts (2x nominal). Stop immediately on a rule/hash mismatch, duplicate accepted query, or surviving rival that changes an actual query; retain the rejected seed/denominator and do not silently clone or shorten. If the time/attempt cap is hit, report the family limit rather than changing policy. No corpus sweep or model job.',
            },
            'coverage_limits': [
                'No sampled family has a retained task-local parametric-rule workspace in this packet; input axes do not establish rule-parameter coverage.',
                'The manifest reports 198 current prototypes among related families; this audit does not validate their settings, hashes or four-query coverage.',
                'Bounded mechanical probes cover one seed and selected indices only; new outputs were not Racket labeled.',
                'Inherited reports remain reviewer-reported or historical as indicated; old relative evidence references do not become current verification.',
                'No retained rejection-rate ledger or review-time telemetry was available in these selected homes; cost and yield extrapolations are explicitly estimates.',
                'Selected executable target code, not archival raw helpers or catalog primitive tokens, defines the inspected grammar.',
                'No blind-solve source/private label was opened, no independent adversarial assignment was drawn, and no sampling weights or approvals were edited.',
            ],
            'source_inventory': inventory,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'report': str(args.out), 'sha256': sha(args.out.read_bytes()),
                      'sampled_ids': ids, 'verified_packet_members': len(inventory),
                      'probe_calls': 21, 'racket_executions': 0}, sort_keys=True))


if __name__ == '__main__':
    main()

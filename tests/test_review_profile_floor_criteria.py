"""Generated duty criteria must match the after command's effective CLI policy."""
import argparse
import ast
import math
from pathlib import Path
import re
import shlex
from types import SimpleNamespace

import pytest

from arcpuzzles.review_full_draw import draw_main
from test_review_full_draw import _packet

ROOT = Path(__file__).resolve().parents[1]


def effective_after_policy(*, exact=60, envelope=60):
    """Exercise the real gate CLI on controlled audit counts, without generation.

    Compile only the actual main function and BANDS constant: import-time rule
    normalizers and the generator/Racket auditor are outside this text-policy
    regression. The real argument parser, rate warnings and exit policy run.
    """
    gate_source = (ROOT / 'shared/tools/canonical_profile_gate.py').read_text()
    tree = ast.parse(gate_source)
    nodes = [node for node in tree.body if
             (isinstance(node, ast.FunctionDef) and node.name == 'main') or
             (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
              target.id == 'BANDS' for target in node.targets))]
    battery = (ROOT / 'shared/tools/run_generator_battery.sh').read_text()
    command = re.search(r'echo "(python3 scripts/canonical_profile_gate.py \$TASK --strict[^"\n]*)"', battery)
    assert command, 'Find the actual strict after profile-floor command'
    argv = shlex.split(command.group(1).replace('$TASK', 'fixture').replace('$pfj', 'unused.json'))[2:]
    # Keep check output in memory; no receipt is needed for a synthetic audit.
    at = argv.index('--json-out')
    del argv[at:at + 2]
    observed = {}

    class Parser(argparse.ArgumentParser):
        def parse_args(self, *args, **kwargs):
            result = super().parse_args(argv)
            observed['args'] = result
            return result

    def audit(task, **kwargs):
        observed['audit_kwargs'] = kwargs
        return {'status': 'PASS', 'draws_total': kwargs['per_band'] * len(namespace['BANDS']),
                'exact_hits': exact, 'envelope_hits': envelope, 'warnings': [], 'errors': []}

    # Supply the real parser subclass without changing argparse's own globals.
    namespace = {'argparse': SimpleNamespace(ArgumentParser=Parser),
                 '__doc__': 'policy regression', 'Path': Path,
                 'ROOT': ROOT, 'audit_task': audit}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-profile-gate-main>', 'exec'), namespace)
    result = namespace['main']()
    return observed['args'], namespace['BANDS'], result


def test_generated_profile_criteria_match_effective_after_defaults(library, tmp_path):
    args, bands, result = effective_after_policy()
    assert result == 0
    assert args.strict and args.require_pass
    packet = _packet(library, tmp_path)
    draw_main(packet, bytes(32))
    duties = ' '.join((packet / 'DUTIES.md').read_text().split())
    total = args.per_band * len(bands)
    assert f'{args.min_band_support} exact canonical-profile hit in each band' in duties
    assert f"each band ({', '.join(bands)})" in duties
    assert f'{args.per_band} draws per band' in duties
    assert f'pooled exact support ≥{args.warn_frac:.0%} ({math.ceil(total * args.warn_frac)}/{total})' in duties
    assert f'pooled envelope support ≥{args.warn_envelope_frac:.0%} ({math.ceil(total * args.warn_envelope_frac)}/{total})' in duties
    assert 'height, width, and distinct-color count' in duties
    assert f'all {total} draws succeed' in duties
    assert 'warnings block' in duties


@pytest.mark.parametrize('exact,envelope,expected', [(3, 15, 0), (3, 14, 1), (2, 15, 1)])
def test_effective_cli_enforces_documented_pooled_boundaries(exact, envelope, expected):
    _, _, result = effective_after_policy(exact=exact, envelope=envelope)
    assert result == expected

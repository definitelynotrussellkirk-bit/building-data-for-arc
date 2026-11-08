"""Native setting contract with a demonstration-only constructive teaching gate."""
import hashlib
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent


def local(name):
    spec = importlib.util.spec_from_file_location('_a251_' + name, BASE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE = local('prototype')
SAMPLER = local('sampler')


def setting(settings):
    if (type(settings) is not dict or set(settings) != {'transfer_scope'}
            or type(settings['transfer_scope']) is not str
            or settings['transfer_scope'] not in CORE.SCOPES):
        raise ValueError('settings require only a valid transfer_scope')
    return settings['transfer_scope']


def program(settings):
    scope = setting(settings)
    return (BASE / ('canonical.rkt' if scope == 'all_templates' else 'largest_template.rkt')).read_text()


def generate(seed, settings, demos, queries):
    scope = setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2 <= demos <= 6 or type(queries) is not int or queries != 4:
        raise ValueError('exact integer seed, 2..6 demos and exactly four queries required')

    def pair(index):
        if index in (0, 1):
            for attempt in range(128):
                draw = seed if attempt == 0 else int.from_bytes(hashlib.sha256(
                    f'a251-teach-v1|{seed}|{index}|{attempt}'.encode()).digest(), 'big')
                grid = SAMPLER.generate(draw, index)
                _, _, templates, _ = CORE.extract(grid)
                largest = max(templates, key=lambda c: templates[c]['size'])
                ordered = list(templates)
                desired = ordered[0] if index == 0 else ordered[-1]
                numeric = max(templates) if index == 0 else min(templates)
                if largest == desired == numeric:
                    break
            else:
                raise ValueError('bounded demonstration construction exhausted')
        else:
            grid = SAMPLER.generate(seed, index)
        return {'input': grid, 'output': CORE.solve(grid, scope)}

    return {'train': [pair(i) for i in range(demos)],
            'test': [pair(100+i) for i in range(4)],
            'program_solution': program(settings)}

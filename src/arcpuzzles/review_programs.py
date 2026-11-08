"""Whole-expression checks shared by editable review helpers, before execution."""
from pathlib import Path


def validate_forms(programs, parser):
    count = 0
    for program in programs:
        count += 1
        if type(program) is not str or not program.strip() or len(program.encode()) > 100000:
            raise ValueError('Program must be nonempty bounded Racket text')
        try:
            forms = parser.parse_all(program)
        except Exception as error:
            raise ValueError('Program requires one complete rule! or lambda expression: ' + str(error)) from error
        if (len(forms) != 1 or type(forms[0]) is not list or not forms[0]
                or forms[0][0] not in (parser.Symbol('rule!'), parser.Symbol('lambda'))):
            raise ValueError('Program requires one complete rule! or lambda expression')
    return {'status': 'passed', 'check': 'one_complete_rule_or_lambda', 'program_count': count}


def strict_programs(root, programs):
    from .parametric_worker import _local_imports
    root = Path(root).resolve(); runtime = root/'shared/runtime'
    path = runtime/'arc_repl/parser.py'
    if (not path.is_file() or not path.resolve().is_relative_to(root)
            or any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root))):
        raise ValueError('Strict program parser must be a regular same-checkout source')
    with _local_imports(runtime, runtime):
        from arc_repl import parser
        if not Path(parser.__file__).resolve().is_relative_to(runtime):
            raise ValueError('Strict program parser must come from the same checkout')
        return validate_forms(programs, parser)


def main(argv=None):
    """Cheap whole-expression check; does not start Racket or qualify a source."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--library', type=Path, default=Path('.'),
                        help='Checkout root containing shared/runtime (default: current directory)')
    parser.add_argument('programs', type=Path, nargs='+', help='Racket program files to check')
    args = parser.parse_args(argv)
    result = strict_programs(args.library, [path.read_text() for path in args.programs])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import print_function

import argparse
import ast
import sys


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('module')
    args = argparser.parse_args()

    lines = list(open(args.module))

    lines_to_bytes = []
    acc = 0
    for line in lines:
        lines_to_bytes.append(acc)
        acc += len(line)

    text = ''.join(lines)

    for item in yield_module_items(text):
        name, line, col = item
        offset = lines_to_bytes[line - 1] + col
        print('{offset: >7,} {name}'.format(
            name=name, offset=offset))

    return True


def yield_module_items(s):
    module = ast.parse(s)
    for c in ast.iter_child_nodes(module):
        fields = dict(ast.iter_fields(c))
        if isinstance(c, ast.FunctionDef):
            yield c.name, c.lineno, c.col_offset + len('def ')
        elif isinstance(c, ast.ClassDef):
            yield c.name, c.lineno, c.col_offset + len('class ')
            for member in fields["body"]:
                if isinstance(member, ast.FunctionDef):
                    mname = '.'.join([c.name, member.name])
                    yield mname, member.lineno, member.col_offset + len('def ')
        elif isinstance(c, ast.Assign):
            yield c


if __name__ == "__main__":
    sys.exit(main())

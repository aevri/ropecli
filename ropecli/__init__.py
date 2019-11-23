#! /usr/bin/env python3
"""A command-line tool for refactoring Python programs."""

import argparse
import ast
import sys

import rope
import rope.base.project
import rope.base.libutils
import rope.refactor.rename
import rope.refactor.move
import rope.refactor.usefunction


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)

    subparsers = parser.add_subparsers()

    # Work around a bug in argparse with subparsers no longer being required:
    # http://bugs.python.org/issue9253#msg186387
    subparsers.required = True
    subparsers.dest = 'command'

    # vulture will report these as unused unless we do this
    #
    # pylint: disable=pointless-statement
    subparsers.required
    subparsers.dest
    # pylint: enable=pointless-statement

    _setup_parser_for_funcs(subparsers, 'move', move_setup, move_do)
    _setup_parser_for_funcs(subparsers, 'rename', rename_setup, rename_do)
    _setup_parser_for_funcs(subparsers, 'list', list_setup, list_do)

    args = parser.parse_args()
    return args.func(args)


def _setup_parser_for_funcs(subparsers, name, setup_func, do_func):
    doc = setup_func.__doc__
    doc_subject = doc.splitlines()[0]
    doc_epilog = '\n'.join(doc.splitlines()[1:])
    parser = subparsers.add_parser(
        name,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=doc_subject,
        description=doc_subject,
        epilog=doc_epilog)
    setup_func(parser)
    parser.set_defaults(func=do_func)


def move_setup(parser):
    """Move items between modules."""
    parser.add_argument('source')
    parser.add_argument('target_file')


def move_do(args):
    project = rope.base.project.Project(
        '.', ropefolder='.clirope')

    filefrom_path, module_item = args.source.split("::")

    filefrom = rope.base.libutils.path_to_resource(
        project, filefrom_path)

    project.validate(filefrom)

    fileto = rope.base.libutils.path_to_resource(
        project, args.target_file)

    project.validate(fileto)

    with open(filefrom_path) as f:
        offset = get_offset_in_file(f, module_item)

    mover = rope.refactor.move.create_move(project, filefrom, offset)
    changes = mover.get_changes(fileto)
    project.do(changes)


def rename_setup(parser):
    """Rename things."""
    parser.add_argument('PATH')
    parser.add_argument('OLD_NAME')
    parser.add_argument('NEW_NAME')


def rename_do(args):
    project = rope.base.project.Project('.', ropefolder='.clirope')

    resource = project.get_resource(args.PATH)
    project.validate(resource)

    with open(args.PATH) as f:
        offset = get_offset_in_file(f, args.OLD_NAME)

    if offset is None:
        print("error: {} not found in {}".format(args.OLD_NAME, args.PATH))
        return 2

    def very_sure(_):
        return True

    renamer = rope.refactor.rename.Rename(project, resource, offset)
    changes = renamer.get_changes(args.NEW_NAME, docs=True, unsure=very_sure)

    project.do(changes)


def list_setup(parser):
    """List entities in a file."""
    parser.add_argument('PATH')


def list_do(args):
    project = rope.base.project.Project('.', ropefolder='.clirope')
    resource = project.get_resource(args.PATH)
    project.validate(resource)
    with open(args.PATH) as f:
        print_offsets(f)


def print_offsets(file_):
    for name, offset in yield_name_offsets(file_):
        print('{offset: >7,} {name}'.format(
            name=name, offset=offset))


def get_offset_in_file(file_, target_name):
    for name, offset in yield_name_offsets(file_):
        if name == target_name:
            return offset
    return None


def yield_name_offsets(file_):
    lines = list(file_)

    lines_to_bytes = []
    acc = 0
    for line in lines:
        lines_to_bytes.append(acc)
        acc += len(line)

    text = ''.join(lines)

    for item in yield_module_items(text):
        name, line, col = item
        offset = lines_to_bytes[line - 1] + col
        yield name, offset


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

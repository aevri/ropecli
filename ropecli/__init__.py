#! /usr/bin/env python3
"""A command-line tool for refactoring Python programs."""

import argparse
import ast
import sys

import click

import rope
import rope.base.project
import rope.base.libutils
import rope.refactor.rename
import rope.refactor.move
import rope.refactor.usefunction


@click.group()
def main():
    pass


@main.command()
@click.argument("source")
@click.argument("target_file", type=click.Path(exists=True, dir_okay=False))
def move(source, target_file):
    project = rope.base.project.Project(".", ropefolder=".clirope")

    filefrom_path, module_item = source.split("::")

    filefrom = rope.base.libutils.path_to_resource(project, filefrom_path)

    project.validate(filefrom)

    fileto = rope.base.libutils.path_to_resource(project, target_file)

    project.validate(fileto)

    with open(filefrom_path) as f:
        offset = get_offset_in_file(f, module_item)

    mover = rope.refactor.move.create_move(project, filefrom, offset)
    changes = mover.get_changes(fileto)
    project.do(changes)


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.argument("old_name")
@click.argument("new_name")
def rename(path, old_name, new_name):
    project = rope.base.project.Project(".", ropefolder=".clirope")

    resource = project.get_resource(path)
    project.validate(resource)

    with open(path) as f:
        offset = get_offset_in_file(f, old_name)

    if offset is None:
        print("error: {} not found in {}".format(old_name, path))
        return 2

    def very_sure(_):
        return True

    renamer = rope.refactor.rename.Rename(project, resource, offset)
    changes = renamer.get_changes(new_name, docs=True, unsure=very_sure)

    project.do(changes)


@main.command(name="list")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def list_command(path):
    # Note that if we called this function 'list', it would collide with the
    # built-in.
    project = rope.base.project.Project(".", ropefolder=".clirope")
    resource = project.get_resource(path)
    project.validate(resource)
    with open(path) as f:
        print_offsets(f)


def print_offsets(file_):
    for name, offset in yield_name_offsets(file_):
        print("{offset: >7,} {name}".format(name=name, offset=offset))


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

    text = "".join(lines)

    for item in yield_module_items(text):
        name, line, col = item
        offset = lines_to_bytes[line - 1] + col
        yield name, offset


def yield_module_items(s):
    module = ast.parse(s)
    for c in ast.iter_child_nodes(module):
        fields = dict(ast.iter_fields(c))
        if isinstance(c, ast.FunctionDef):
            yield c.name, c.lineno, c.col_offset + len("def ")
        elif isinstance(c, ast.ClassDef):
            yield c.name, c.lineno, c.col_offset + len("class ")
            for member in fields["body"]:
                if isinstance(member, ast.FunctionDef):
                    mname = ".".join([c.name, member.name])
                    yield mname, member.lineno, member.col_offset + len("def ")
        elif isinstance(c, ast.Assign):
            yield c

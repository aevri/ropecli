#! /usr/bin/env python3
"""A command-line tool for refactoring Python programs."""

import ast
import fnmatch
import pathlib
import sys

import click
import rope.base.libutils
import rope.base.project
import rope.refactor.importutils
import rope.refactor.move
import rope.refactor.rename


# Note that we can easily support the following import refactors, along the
# lines of 'organize_imports' and 'froms_to_imports':
#
#  o: expand_stars
#  o: handle_long_imports
#  o: relatives_to_absolutes
#  o: sort_imports
#

# We can sort of implement command aliases in Click like so:
# https://stackoverflow.com/questions/46641928/python-click-multiple-command-names


@click.group()
def main():
    """A refactoring tool for Python programs.

    Built on the excellent 'rope' refactoring library, which powers the
    refactoring capabilities of a number of IDEs.
    """
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def froms_to_imports(path):
    """Change the 'from X import Y' statements in PATH to 'import X.Y'.

    e.g.

      rope froms-to-imports mypackage/mymodule.py

    """
    project = rope.base.project.Project(".", ropefolder=".clirope")

    resource = project.get_resource(path)
    pymodule = project.get_pymodule(resource)
    project.validate(resource)

    tools = rope.refactor.importutils.ImportTools(project)
    new_content = tools.froms_to_imports(pymodule)

    pathlib.Path(path).write_text(new_content)


@main.command(name="list")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def list_command(path):
    """List the global entities in PATH.

    This will show things that might be used as arguments in invocations of
    other commands.
    """
    # Note that if we called this function 'list', it would collide with the
    # built-in.
    project = rope.base.project.Project(".", ropefolder=".clirope")
    resource = project.get_resource(path)
    project.validate(resource)
    with open(path) as f:
        print_offsets(f)


@main.command()
@click.argument("source")
@click.argument("target_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--glob/--no-glob",
    default=True,
    help="Apply globbing to the second part of 'source'.",
)
@click.option(
    "--exclude",
    "-e",
    help="Exclude this from list of sources, can be specified multiple times. Globbing rules apply.",
    multiple=True,
)
def move(source, target_file, glob, exclude):
    """Move the global entry SOURCE to the TARGET_FILE.

    All references to the entry will be adjusted to refer to the new location.

    e.g.

      \b
      # Move "MyClass" from modulea.py to moduleb.py
      rope move modulea.py::MyClass moduleb.py

      \b
      # Move all things that start with "Thingy" from modulea.py to thingy.py
      rope move modulea.py::Thingy* thingy.py

      \b
      # Move all things that start with "Thingy" from modulea.py to thingy.py,
      # except for "ThingyB":
      rope move modulea.py::Thingy* thingy.py --exclude *::ThingyB

    """
    project = rope.base.project.Project(".", ropefolder=".clirope")

    source_list = [source]
    if glob:
        source_list = list(glob_resourcespec(source))

    for pattern in exclude:
        old_source_list = source_list
        source_list = []
        for current_source in old_source_list:
            if fnmatch.fnmatchcase(current_source, pattern):
                continue
            source_list.append(current_source)
        if len(old_source_list) == len(source_list):
            click.echo(
                f"Warning: exclude pattern '{pattern}' didn't match anything.",
                err=True,
            )

    if not source_list:
        click.echo("Nothing to do.", err=True)
    elif len(source_list) == 1:
        do_move(project, source_list[0], target_file)
    else:
        with click.progressbar(
            source_list, file=sys.stderr, item_show_func=str
        ) as bar:
            for current_source in bar:
                do_move(project, current_source, target_file)


def do_move(project, source, target_file):
    filefrom, offset = resourcespec_to_resource_offset(project, source)

    fileto = project.get_resource(target_file)

    mover = rope.refactor.move.create_move(project, filefrom, offset)
    changes = mover.get_changes(fileto)
    project.do(changes)


def resourcespec_to_resource_offset(project, resourcespec):
    if "::" in resourcespec:
        file_path, module_item = resourcespec.split("::")
    else:
        file_path = resourcespec
        module_item = None
    file_resource = project.get_resource(file_path)

    if module_item is not None:
        with open(file_path) as f:
            offset = get_offset_in_file(f, module_item)
    else:
        offset = None

    return file_resource, offset


def glob_resourcespec(resourcespec):
    if "::" not in resourcespec:
        raise ValueError(f"'{resourcespec}' does not contain '::'")
    file_path, pattern = resourcespec.split("::")
    for name in yield_module_path_itemnames(file_path, only_toplevel=True):
        if fnmatch.fnmatchcase(name, pattern):
            yield f"{file_path}::{name}"


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def organize_imports(path):
    """Organize the import statements in PATH in an opinionated way.

    In particular; unused or duplicate imports will be dropped, imports will be
    sorted and grouped, and the standard import group will appear first.

    e.g.

      rope organize_imports mypackage/mymodule.py

    """
    project = rope.base.project.Project(".", ropefolder=".clirope")

    resource = project.get_resource(path)
    pymodule = project.get_pymodule(resource)
    project.validate(resource)

    tools = rope.refactor.importutils.ImportTools(project)
    new_content = tools.organize_imports(pymodule)

    pathlib.Path(path).write_text(new_content)


@main.command()
@click.argument("target")
@click.argument("new_name")
@click.option("--dry-run/--no-dry-run", default=False)
def rename(target, new_name, dry_run):
    """Rename the global entry TARGET to NEW_NAME.

    All references to the entry will be adjusted to refer to the new name,
    including in documentation.

    e.g.

      rope rename modulea.py::MyClass MyAwesomeClass

    or

      rope rename modulea.py moduleb

    """
    project = rope.base.project.Project(".", ropefolder=".clirope")

    resource, offset = resourcespec_to_resource_offset(project, target)

    def very_sure(_):
        return True

    renamer = rope.refactor.rename.Rename(project, resource, offset)
    changes = renamer.get_changes(new_name, docs=True, unsure=very_sure)

    if dry_run:
        print(changes.get_description())
    else:
        project.do(changes)


def print_offsets(file_):
    for name, offset in yield_name_offsets(file_):
        print("{offset: >7,} {name}".format(name=name, offset=offset))


def get_offset_in_file(file_, target_name):
    for name, offset in yield_name_offsets(file_):
        if name == target_name:
            return offset
    raise KeyError(f"'{target_name}' does not exist in the supplied file.")


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


def yield_module_path_itemnames(file_path, only_toplevel=False):
    text = pathlib.Path(file_path).read_text()
    for name, _, _ in yield_module_items(text, only_toplevel):
        yield name


def yield_module_items(s, only_toplevel=False):
    module = ast.parse(s)
    for c in ast.iter_child_nodes(module):
        fields = dict(ast.iter_fields(c))
        if isinstance(c, ast.FunctionDef):
            yield c.name, c.lineno, c.col_offset + len("def ")
        elif isinstance(c, ast.ClassDef):
            yield c.name, c.lineno, c.col_offset + len("class ")
            if only_toplevel:
                continue
            for member in fields["body"]:
                if isinstance(member, ast.FunctionDef):
                    mname = ".".join([c.name, member.name])
                    yield mname, member.lineno, member.col_offset + len("def ")
        elif isinstance(c, ast.Assign):
            yield c


# -----------------------------------------------------------------------------
# Copyright (C) 2019 Angelos Evripiotis.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------

import pathlib

import click.testing

import ropecli


VEGETABLES_PY = """
from sys import stderr
import argparse


def carrots():
    print("carrots!", file=stderr)


def tomatoes():
    print("tomatoes!")


def all():
    carrots()
    tomatoes()
"""

FRUIT_PY = """
def cherries():
    print("cherries!")
"""


def make_veg_fruit_pyfiles():
    veg = pathlib.Path("veg.py")
    veg.write_text(VEGETABLES_PY)
    fruit = pathlib.Path("fruit.py")
    fruit.write_text(FRUIT_PY)
    return veg, fruit


def run(runner, *args):
    str_args = [str(a) for a in args]
    result = runner.invoke(ropecli.main, str_args)
    print(result.stdout)
    # It seems that the "mix_stderr" parameter to CliRunner() is not working as
    # expected, so everything will come out on stdout for now.
    # print(result.stderr, file=sys.stderr)

    assert result.exit_code == 0

    return result


def test_smoketest():
    # Make sure we can do the bare minimum without an error.
    runner = click.testing.CliRunner()
    assert runner.invoke(ropecli.main).exit_code == 0


def test_help():
    runner = click.testing.CliRunner()
    run(runner, "--help")
    for command in ropecli.main.list_commands(ctx=None):
        run(runner, command, "--help")


def test_froms_to_imports_simple():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        veg, fruit = make_veg_fruit_pyfiles()
        assert "from sys import stderr" in veg.read_text()
        run(runner, "froms-to-imports", veg)
        assert "from sys import stderr" not in veg.read_text()


def test_list_simple():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        veg, fruit = make_veg_fruit_pyfiles()
        result = run(runner, "list", fruit)
        assert "cherries" in result.stdout


def test_move_simple():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        veg, fruit = make_veg_fruit_pyfiles()
        assert "fruit.tomatoes()" not in veg.read_text()
        assert "def tomatoes()" not in fruit.read_text()
        run(runner, "move", f"{veg}::tomatoes", fruit)
        assert "fruit.tomatoes()" in veg.read_text()
        assert "def tomatoes()" in fruit.read_text()


def test_organize_imports_simple():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        veg, fruit = make_veg_fruit_pyfiles()
        assert "import argparse" in veg.read_text()
        run(runner, "organize-imports", veg)
        assert "import argparse" not in veg.read_text()


def test_rename_simple():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        veg, fruit = make_veg_fruit_pyfiles()
        assert "def tomafingers()" not in veg.read_text()
        assert "    tomafingers()" not in veg.read_text()
        run(runner, "rename", veg, "tomatoes", "tomafingers")
        assert "def tomafingers()" in veg.read_text()
        assert "    tomafingers()" in veg.read_text()


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

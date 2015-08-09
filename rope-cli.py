import argparse
import sys

sys.path.append('/home/angelos/repos/rope')
import rope
import rope.base.project
import rope.base.libutils
import rope.refactor.rename
import rope.refactor.move


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('fromfile')
    argparser.add_argument('offset', type=int)
    argparser.add_argument('tofile')
    args = argparser.parse_args()

    print 'rope version: ', rope.VERSION

    project = rope.base.project.Project(
        '.', ropefolder='.testrope')

    filefrom = rope.base.libutils.path_to_resource(
        project, args.fromfile)

    project.validate(filefrom)

    fileto = rope.base.libutils.path_to_resource(
        project, args.tofile)

    project.validate(fileto)

    # renamer = rope.refactor.rename.Rename(project, filea, 5)
    # changes = renamer.get_changes('do_wop')
    # print changes.get_description()
    # project.do(changes)

    mover = rope.refactor.move.create_move(project, filefrom, args.offset)
    changes = mover.get_changes(fileto)
    print changes.get_description()
    # help(mover)


if __name__ == "__main__":
    sys.exit(main())

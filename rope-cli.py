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
    argparser.add_argument('--force', '-f', action='store_true')
    args = argparser.parse_args()

    project = rope.base.project.Project(
        '.', ropefolder='.clirope')

    filefrom = rope.base.libutils.path_to_resource(
        project, args.fromfile)

    project.validate(filefrom)

    fileto = rope.base.libutils.path_to_resource(
        project, args.tofile)

    project.validate(fileto)

    mover = rope.refactor.move.create_move(project, filefrom, args.offset)
    changes = mover.get_changes(fileto)
    if args.force:
        project.do(changes)
    else:
        print changes.get_description()


if __name__ == "__main__":
    sys.exit(main())

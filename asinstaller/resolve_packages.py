"""Helps resolve which ArchStrike packages can be installed without error"""
import argparse
import sys
import pyalpm
import pycman
import logging
import collections
logging.basicConfig(format='%(message)s', level=logging.DEBUG, handlers=[logging.NullHandler()])
stdout = logging.getLogger('stdout')
stdout.addHandler(logging.StreamHandler(sys.stdout))
stderr = logging.getLogger('stderr')
stderr.addHandler(logging.StreamHandler(sys.stderr))


__all__ = ['PackageArbiter', 'main']


class FlatDepends(object):
    def __init__(self):
        self.conflicts = set([])
        self.depends = set([])


flatdepends = collections.defaultdict(FlatDepends)


def get_packages_depending_on(flatdepends, pkgname):
    return [pkg for pkg, info in flatdepends.items() if pkgname in info.depends]


def get_group_packages(repos, name):
    for repo in repos.values():
        grp = repo.read_grp(name)
        if grp is None:
            continue
        name, pkgs = grp
        return pkgs


def find_satisfier(repos, pkg):
    for syncdb in repos.values():
        satisfier = pyalpm.find_satisfier(syncdb.pkgcache, pkg)
        if satisfier is not None:
            return satisfier


def find_missing_depends(repos, root, deps):
    global flatdepends
    missing = set([])
    for dep in deps:
        flatdepends[root].depends.add(dep)
        satisfier = find_satisfier(repos, dep)
        if satisfier is None:
            missing.add(dep)
            continue
        for replaced in satisfier.replaces:
            flatdepends[root].depends.add(replaced)
        for provided in satisfier.provides:
            flatdepends[root].depends.add(provided)
        for conflict in set(satisfier.conflicts) - flatdepends[root].depends:
            flatdepends[root].conflicts.add(conflict)
        recurse_deps = [d for d in satisfier.depends if d not in flatdepends[root].depends]
        for subtree_dep in find_missing_depends(repos, root, recurse_deps):
            missing.add(subtree_dep)
    return missing


def irresolvable_depends(repos, pkgs):
    for pkg in pkgs:
        missing_depends = find_missing_depends(repos, pkg.name, pkg.depends)
        if missing_depends:
            yield pkg.name, missing_depends


def irresolvable_depends_from_file(repos, filename):
    if filename:
        for line in open(filename):
            line = line.strip()
            if line.startswith('#') or len(line) == 0:
                continue
            for pkgname in line.split(' '):
                okay, pkg = pycman.action_sync.find_sync_package(pkgname, repos)
                if not okay:  # make sure not a group before saying it's missing
                    grp_pkgs = get_group_packages(repos, pkgname)
                    if grp_pkgs:
                        for pkgname, deps in irresolvable_depends(repos, grp_pkgs):
                            yield pkgname, deps
                    else:
                        yield pkgname, [f'(error: {pkg})']
                else:
                    missing_deps = find_missing_depends(repos, pkg.name, pkg.depends)
                    if missing_deps:
                        yield pkg.name, missing_deps


def conflicting_pactrees(flatdepends):
    """Check for conflicts pair-wise in the dependency tree"""
    package_conflicts = collections.defaultdict(set)
    for pkg_i, flatdep_i in flatdepends.items():
        for pkg_j, flatdep_j in flatdepends.items():
            if pkg_i == pkg_j:
                continue
            deps_i = flatdep_i.depends
            conflicts_j = flatdep_j.conflicts
            if pkg_i in conflicts_j:
                package_conflicts[pkg_i].add(pkg_j)

            for conflict in deps_i.intersection(conflicts_j):
                package_conflicts[pkg_j].add(pkg_i)
                package_conflicts[conflict].add(pkg_i)
    return package_conflicts


def column_width(lhs_title, values):
    width = len(lhs_title)
    for val in values:
        width = max(width, len(val))
    return width


def show_irresolvable_depends(pkg_missing_depends, origin, rhs="Package depends"):
    if not pkg_missing_depends:
        return
    stderr.error("")
    # Find padding
    SEP = " " * 4
    lhs = f"Irresolvable {origin}"
    width = column_width(lhs, pkg_missing_depends) + len(SEP)
    # Header
    stderr.error(f"{lhs:<{width}}{rhs}")
    for pkg, missing_depends in pkg_missing_depends.items():
        err_depends = " ".join(missing_depends)
        stderr.error(f"\033[1;31m{pkg:<{width}}{err_depends}\033[m")


def get_args():
    parser = argparse.ArgumentParser(description='Robust ArchStrike group analysis and installer')
    parser.add_argument('--file', type=str, help='Specify a file with a list of package names')
    parser.add_argument('--group', type=str, default='archstrike',
                        help='Specify an alternate pacman configuration file')
    parser.add_argument('--config', type=str, default='/etc/pacman.conf',
                        help='Specify an alternate pacman configuration file')
    return parser.parse_args()


class Packages(object):
    """hides complexity of underlying types"""
    def __init__(self, packages):
        self.packages = packages

    def __str__(self):
        return ' '.join([pkg.name for pkg in self.packages])


class PackageArbiter(object):
    def __init__(self, args=None):
        self.groupname = getattr(args, 'group', 'archstrike')
        self.file = getattr(args, 'file', None)
        self.config = getattr(args, 'config', '/etc/pacman.conf')
        self.dbnames = set(['core', 'extra', 'community', 'multilib', 'archstrike', 'archstrike-testing'])
        self.pacman_config = pycman.config.PacmanConfig(conf=self.config)
        self.hpacman = self.pacman_config.initialize_alpm()
        self._repos = None
        self._group_pkgs = None
        self._bad_group_pkgs = None
        self._bad_file_pkgs = None
        self._conflicted_trees = None
        self._resolvable_group_pkgs = None

    @property
    def repos(self):
        if self._repos is None:
            self._repos = dict((db.name, db) for db in self.hpacman.get_syncdbs() if db.name in self.dbnames)
        return self._repos

    @property
    def group_pkgs(self):
        if self._group_pkgs is None:
            self._group_pkgs = get_group_packages(self.repos, self.groupname)
        return self._group_pkgs

    @property
    def bad_group_pkgs(self):
        if self._bad_group_pkgs is None:
            self._bad_group_pkgs = {p: m for p, m in irresolvable_depends(self.repos, self.group_pkgs)}
        return self._bad_group_pkgs

    @property
    def bad_file_pkgs(self):
        if self._bad_file_pkgs is None:
            self._bad_file_pkgs = {p: m for p, m in irresolvable_depends_from_file(self.repos, self.file)}
        return self._bad_file_pkgs

    @property
    def conflicted_trees(self):
        if self._conflicted_trees is None:
            self._conflicted_trees = conflicting_pactrees(flatdepends)
        return self._conflicted_trees

    @property
    def resolvable_group_pkgs(self):
        if self._resolvable_group_pkgs is None:
            # Resolving two conflicting pactrees is non-trivial. So, remove all root packages
            # that have a conflicting dependency tree with at least other package.
            exclusions = set([])
            for irresolvable in [self.bad_group_pkgs, self.conflicted_trees]:
                for pkg, missing_deps in irresolvable.items():
                    exclusions.add(pkg)
                    for dep in missing_deps:
                        exclusions.add(dep)
            self._resolvable_group_pkgs = Packages([pkg for pkg in self.group_pkgs if pkg.name not in exclusions])
        return self._resolvable_group_pkgs


def main():
    """entry point for bin/archstrike-arbitration"""
    args = get_args()
    arbiter = PackageArbiter(args)
    # Show results
    stdout.info(arbiter.resolvable_group_pkgs)
    show_irresolvable_depends(arbiter.bad_group_pkgs, "archstrike")
    show_irresolvable_depends(arbiter.bad_file_pkgs, "file")
    show_irresolvable_depends(arbiter.conflicted_trees, "tree", "Conflicts")

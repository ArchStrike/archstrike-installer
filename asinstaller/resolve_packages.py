"""Helps resolve which ArchStrike packages can be installed without error"""
import argparse
import sys
import pathlib
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
package_not_found = '"package not found"'


def get_packages_depending_on(flatdepends, pkgname):
    return [pkg for pkg, info in flatdepends.items() if pkgname in info.depends]


def get_group_packages(repos, name):
    if not name:
        return []
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


def packagenames_from_file(repos, filenames):
    for filename in filenames:
        if filename:
            fpath = pathlib.Path(filename)
            if not fpath.is_file():
                stderr.error(f"File not found: '{filename}'...")
                continue
            for line in fpath.open():
                line = line.strip()
                if line.startswith('#'):
                    continue
                for pkgname in line.split(' '):
                    if len(pkgname) == 0:
                        continue
                    yield pkgname


def iter_pkgname_package(repos, pkgnames):
    for pkgname in pkgnames:
        okay, pkg = pycman.action_sync.find_sync_package(pkgname, repos)
        if not okay:  # make sure not a group before saying it's missing
            grp_pkgs = get_group_packages(repos, pkgname)
            if grp_pkgs:
                for pkg in grp_pkgs:
                    yield pkg.name, pkg
            else:
                yield pkgname, None
        else:
            yield pkg.name, pkg


def irresolvable_depends(repos, pkgname_package):
    for pkgname, pkg in pkgname_package.items():
        if pkg is None:
            yield pkgname, [package_not_found]
        else:
            missing_depends = find_missing_depends(repos, pkg.name, pkg.depends)
            if missing_depends:
                yield pkg.name, missing_depends


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
    parser.add_argument('--file', nargs='+', help='Specify at least one file containing a list of package names')
    parser.add_argument('--package', nargs='+', help='Specify packages to check')
    parser.add_argument('--config', type=str, default='/etc/pacman.conf',
                        help='Specify an alternate pacman configuration file')
    return parser.parse_args()


class Packages(object):
    """hides complexity of underlying types"""
    def __init__(self, packages):
        self.packages = packages

    def __str__(self):
        return ' '.join(list(self.packages))


class PackageArbiter(object):
    def __init__(self, args=None):
        self._arg_files = [] if getattr(args, 'file', None) is None else args.file
        self._arg_packages = set([]) if getattr(args, 'package', None) is None else set(args.package)
        self.config = getattr(args, 'config', '/etc/pacman.conf')
        self.dbnames = set(['core', 'extra', 'community', 'multilib', 'archstrike', 'archstrike-testing'])
        self.pacman_config = pycman.config.PacmanConfig(conf=self.config)
        self.hpacman = self.pacman_config.initialize_alpm()
        self._repos = None
        self._packages = None
        self._irresolvable_packages = None
        self._conflicted_packages = None
        self._bad_pkgnames = None
        self._good_packages = None

    @property
    def repos(self):
        if self._repos is None:
            self._repos = dict((db.name, db) for db in self.hpacman.get_syncdbs() if db.name in self.dbnames)
        return self._repos

    @property
    def packages(self):
        if self._packages is None:
            self._packages = self._arg_packages
            for pkg in packagenames_from_file(self.repos, self._arg_files):
                self._packages.add(pkg)
            self._packages = {n: p for n, p in iter_pkgname_package(self.repos, self._packages)}
        return self._packages

    @property
    def irresolvable_packages(self):
        if self._irresolvable_packages is None:
            self._irresolvable_packages = {n: m for n, m in irresolvable_depends(self.repos, self.packages)}
        return self._irresolvable_packages

    @property
    def conflicted_packages(self):
        if self._conflicted_packages is None:
            self._conflicted_packages = conflicting_pactrees(flatdepends)
        return self._conflicted_packages

    @property
    def bad_pkgnames(self):
        if self._bad_pkgnames is None:
            self._bad_pkgnames = set([])
            # Resolving two conflicting pactrees takes some mental gymnastics. So, remove all root packages
            # that have a conflicting dependency tree with at least other package.
            for irresolvable in [self.irresolvable_packages, self.conflicted_packages]:
                for pkg, missing_deps in irresolvable.items():
                    self._bad_pkgnames.add(pkg)
                    for dep in missing_deps:
                        self._bad_pkgnames.add(dep)
        return self._bad_pkgnames

    @property
    def good_packages(self):
        if self._good_packages is None:
            self._good_packages = {n: p for n, p in self.packages.items() if n not in self.bad_pkgnames}
            self._good_packages = Packages(self._good_packages)
        return self._good_packages


def main():
    """entry point for bin/archstrike-arbitration"""
    args = get_args()
    arbiter = PackageArbiter(args)
    # Show results
    stdout.info(arbiter.good_packages)
    show_irresolvable_depends(arbiter.irresolvable_packages, "package", "Dependencies")
    show_irresolvable_depends(arbiter.conflicted_packages, "pactree", "Conflicts")

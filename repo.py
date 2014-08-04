import os

from dulwich import repo
from subprocess import check_output


class SohuRepo(repo.Repo):

    DEFAULT_BRANCH = 'master'

    @property
    def name(self):
        return self.path.replace('.git', '').rstrip(os.sep).split(os.sep)[-1]

    def history(self, commit, path=None, max_commits=None, skip=0):
        """
        Returns a list of all commits that infected `path`, starting at branch
        or commit `commit`. `skip` can be used for pagination, `max_commits`
        to limit the number of commits returned.

        Similar to `git log [branch/commit] [--skip skip] [-n max_commits]`.
        """
        # XXX The pure-Python/dulwich code is very slow compared to `git log`
        #     at the time of this writing (mid-2012).
        #     For instance, `git log .tx` in the Django root directory takes
        #     about 0.15s on my machine whereas the history() method needs 5s.
        #     Therefore we use `git log` here until dulwich gets faster.
        #     For the pure-Python implementation, see the 'purepy-hist' branch.

        cmd = ['git', 'log', '--format=%H']
        if skip:
            cmd.append('--skip=%d' % skip)
        if max_commits:
            cmd.append('--max-count=%d' % max_commits)
        cmd.append(commit)
        if path:
            cmd.extend(['--', path])

        sha1_sums = check_output(cmd, cwd=os.path.abspath(self.path))
        return [self[sha1] for sha1 in sha1_sums.strip().split('\n')]


class GitRepository(object):

    DEFAULT_BRANCH = 'master'

    def __init__(self, repo_path, bare=False):
        self.path = os.path.abspath(repo_path)
        self.repo = self.get_repo(bare)

    def get_repo(self, bare=False):
        try:
            os.makedirs(self.path)
        except Exception, e:
            print Exception("This folder is already in use.")
        try:
            return SohuRepo(self.path)
        except Exception, e:
            print Exception("This folder is already in use, and it's not a git repo.")
        if bare:
            return SohuRepo.init_bare(self.path)
        else:
            return SohuRepo.init(self.path)
        pass

if __name__ == '__main__':
    repo1 = GitRepository('Crotal', bare=True)
    print repo1.repo.name
    print repo1.repo.history('master', max_commits=5, skip=3)

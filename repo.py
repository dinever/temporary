import os

import dulwich
from dulwich import repo
from subprocess import check_output


class SohuRepo(repo.Repo):

    DEFAULT_BRANCH = 'master'

    @property
    def name(self):
        return self.path.replace('.git', '').rstrip(os.sep).split(os.sep)[-1]

    def get_commit(self, rev):
        rev = str(rev)  # https://github.com/jelmer/dulwich/issues/144
        for prefix in ['refs/heads/', 'refs/tags/', '']:
            key = prefix + rev
            try:
                obj = self[key]
                if isinstance(obj, dulwich.objects.Tag):
                    obj = self[obj.object[1]]
                return obj
            except KeyError:
                pass
        raise KeyError(rev)

    def get_blob_or_tree(self, commit, path):
        tree_or_blob = self[commit.tree]
        for part in path.strip('/').split('/'):
            if part:
                if isinstance(tree_or_blob, dulwich.objects.Blob):
                    raise KeyError
                tree_or_blob = self[tree_or_blob[part][1]]
        return tree_or_blob

    def history(self, commit, path=None, max_commits=None, skip=0):
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

    def get_sorted_ref_names(self, prefix, exclude=None):
        refs = self.refs.as_dict(prefix)
        if exclude:
            refs.pop(prefix + exclude, None)

        def get_commit_time(refname):
            obj = self[refs[refname]]
            if isinstance(obj, dulwich.objects.Tag):
                return obj.tag_time
            return obj.commit_time

        return sorted(refs.iterkeys(), key=get_commit_time, reverse=True)

    def get_branch_names(self, exclude=None):
        """ Returns a sorted list of branch names. """
        return self.get_sorted_ref_names('refs/heads', exclude)


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

    def get_a_file(self, rev, path):
        try:
            commit = self.repo.get_commit(rev)
        except Exception, e:
            raise Exception
        blob = self.repo.get_blob_or_tree(commit, path)
        return blob


if __name__ == '__main__':
    repo1 = GitRepository('Crotal', bare=True)
    print repo1.repo.name
    print repo1.repo.history('master', max_commits=5, skip=3)
    print repo1.repo.get_commit('dc3ea256596516821f846a3c58e7886a2d2695d2')
    repo1.get_a_file('dc3ea256596516821f846a3c58e7886a2d2695d2', 'README.md')
    print repo1.repo.get_branch_names()

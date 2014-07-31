import os

from dulwich.repo import Repo

class GitRepository(object):

    def __init__(self, repo_path):
        self.path = os.abspath(repo_path)

    def get_repo(self):
        os.mkdirs(self.path)
        if bare:
            return Repo.init_bare(self.path)
        else:
            return Repo.init(self.path)
        pass

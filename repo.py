import os

from dulwich.repo import Repo

class GitRepository(object):

    def __init__(self, repo_path, bare=False):
        self.path = os.path.abspath(repo_path )
        self.repo = self.get_repo(bare)

    def get_repo(self, bare=False):
        try:
            os.makedirs(self.path)
        except Exception, e:
            raise Exception('This folder is already in use.')
        if bare:
            return Repo.init_bare(self.path)
        else:
            return Repo.init(self.path)
        pass

if __name__ == '__main__':
    repo1 = GitRepository('hello', bare=True)
    new_file = open('hello/newfile', 'w+')
    new_file.write('This is a new_file')
    new_file.close()
    repo1.repo.stage(['newfile'])

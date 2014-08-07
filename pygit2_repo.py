#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import pprint
import pygit2
import time
from subprocess import check_output


class Repo(pygit2.Repository):

    @property
    def name(self):
        return self.path.replace('.git', '').rstrip(os.sep).split(os.sep)[-1]

    def get_history(self):
        commit_history = []
        last = self[self.head.target]
        for commit in repo.walk(last.id, pygit2.GIT_SORT_TIME):
            commit_history.append(commit)
        return commit_history


class Git(object):
    def __init__(self, path):
        self.path = path
        self.repo = Repo(path)

    def is_empty(self):
        return self.repo.is_empty

    def _get_refs(self):
        refs = {
            'branches': [],
            'tags': [],
            'head': self.repo.head.target,
            }
        all_refs = self.repo.listall_references()
        for i in all_refs:
            if i.startswith('refs/heads/'):
                ref = self.repo.lookup_reference(i)
                commit = self.repo[ref.target]
                refs['branches'].append((i[11:], commit))
            if i.startswith('refs/tags/'):
                ref = self.repo.lookup_reference(i)
                tag = self.repo[ref.target]
                commit = self.repo[tag.target]
                refs['tags'].append((i[10:], tag, commit))
        return refs

    def get_history_old(self, count=None, skip=0):
        commit_history = list()
        history_walker = self.repo.walk(self.repo.head.target, pygit2.GIT_SORT_TIME)
        for i, commit in enumerate(history_walker):
            if i < skip:
                continue
            if i == skip + count:
                return commit_history
            else:
                commit_history.append(commit)
        return commit_history

    def get_history(self, commit, path=None, max_commits=None, skip=0):
        '''
        pygit2自身的Repository类下带有walk函数，可以返回一个commit迭代器，用来遍历commit，
        但在使用过程中，我发现用pygit2提供的迭代器来获取commit非常慢，在对Django官方Github库
        取第3000-3050个commit时，pygit2耗时0.255秒，而用本方法只需要0.032秒。
        :param commit: 可以是commit_id，也可以是分支名
        :param path: 若指定path，则会根据path对应的文件查看其历史commit
        :param max_commits: 返回的commit数量
        :param skip: 跳过之前多少个commit，这一参数在分页时可以用到
        :return: 返回一个commit list
        '''
        cmd = ['git', 'log', '--format=%H']
        if skip:
            cmd.append('--skip=%d' % skip)
        if max_commits:
            cmd.append('--max-count=%d' % max_commits)
        cmd.append(commit)
        if path:
            cmd.extend(['--', path])
        sha1_sums = check_output(cmd, cwd=os.path.abspath(self.path))
        if sha1_sums == '':
            return [] # 没有符号条件的commit
        else:
            return [self.repo[sha1] for sha1 in sha1_sums.strip().split('\n')]

    # def get_commit(self, cid=''):
    #     refs = self._get_refs()
    #     ctx = {"project": self.repo}
    #     if cid == '':
    #         commit = self.repo[self.repo.head.target]
    #     else:
    #         commit = self.repo[unicode(cid)]
    #     ctx['commit'] = commit
    #     ctx['refs'] = refs
    #
    #     if len(commit.parents) > 0:
    #         commit_b = self.repo[commit.parents[0].hex]
    #         diff = commit_b.tree.diff_to_tree(commit.tree)
    #         try:
    #             ctx['patch'] = diff.patch.decode('utf-8')
    #         except UnicodeDecodeError:
    #             ctx['patch'] = diff.patch
    #     else:
    #         tb = self.repo.TreeBuilder()
    #         diff = self.repo[tb.write()].diff(commit.tree)
    #     return ctx

    def get_commit(self, cid=''):
        if cid == '':
            commit = self.repo[self.repo.head.target]
        else:
            commit = self.repo[unicode(cid)]
        return commit

    def get_tree(self, commit='', path=''):
        commit = 'develop'
        if not isinstance(commit, pygit2.Commit):
            try:
                commit = self.get_commit(commit)
                tree = commit.tree
            except:
                branch = commit
                tree = self.repo.revparse_single(branch).tree
        return tree

    def get_all_files(self, branch='master'):
        files = []
        tree = self.repo.revparse_single(branch).tree
        for entry in tree:
            commit = self.repo.revparse_single(str(entry.id))
            commit = self.get_commit(str(entry.id))
        obj = self.repo['414b218cbd908ab7829d1e51b49d4aa989d392a3']
        print obj.commit
        return files

    def get_file(self, filepath):
        index = self.repo.index
        index.read()
        id = index[filepath].oid
        blob = self.repo[id]
        return {
            'size': blob.size,
            'data': blob.data,
            'is_binary': blob.is_binary,
        }

    def diff_two_commits(self, commit, from_commit, **kwargs):
        tree = commit.tree
        from_tree = from_commit.tree
        if from_tree:
            diff = self.repo.diff(from_tree, tree, **kwargs)
            old_sha = from_commit.hex
        else:
            diff = tree.diff_to_tree(swap=True, **kwargs)
            old_sha = None
        return diff, old_sha

    def get_commits_diff(self, commit, from_commit=None, **kwargs):
        if from_commit is None:
            parents = commit.parents
            if len(parents) == 1:
                diff = self.diff_two_commits(commit, parents[0])
        else:
            diff = self.diff_two_commits(commit, from_commit)
        return diff

    def diff_patches(self, commit, from_commit=None, **kwargs):
        """
        :param commit:
        :param from_commit:
        :param kwargs:
        :return:
        [{'additions': 8, # 新增加的行数
          'deletions': 1, # 删除的行数
          'hunks': [{'lines': [(u' ', u'import yaml\n'), # 未改动的行
                               (u' ', u'import os.path\n'),
                               (u'+', u'\n'), # 新增加的行
                               (u' ', u'class Config():\n'),
                               (u'+', u'\n'),
                               (u'-', u"print 'hello world"), # 删去的行
                     'new_lines': 20, # 新文件的行数
                     'new_start': 1, # 第一个新增加的行的所在行数
                     'old_lines': 13, # 旧文件的行数
                     'old_start': 1}], # 第一个删除的行的所在行数
          'new_file_path': 'crotal/config.py', # 新文件路径
          'old_file_path': 'crotal/config.py', # 就文件路径
          'status': 'M'}]
        """
        diff = self.get_commits_diff(commit, from_commit)[0]
        patches = [p for p in diff]
        changes = []
        for patch in patches:
            hunks_list = []
            for hunk in patch.hunks:
                hunk_dict = {
                    'old_start': hunk.old_start,
                    'new_start': hunk.new_start,
                    'old_lines': hunk.old_lines,
                    'new_lines': hunk.new_lines,
                    'lines': hunk.lines,
                }
            hunks_list.append(hunk_dict)
            patch_dict = {
                'old_file_path': patch.old_file_path,
                'additions': patch.additions,
                'new_file_path': patch.new_file_path,
                'deletions': patch.deletions,
                'status': patch.status,
                'hunks': hunks_list,
            }
            changes.append(patch_dict)
        return changes

    def diff_commits_by_cid(self, cid, from_cid=None, **kwargs):
        commit = self.get_commit(cid).get('commit')
        old_commit = self.get_commit(from_cid).get('commit') if from_cid else None
        return self.diff_patches(commit, old_commit)

    @staticmethod
    def clone_repository(url, path, **kwargs):
        pygit2.clone_repository(url, path, **kwargs)

    def get_status(self):
        return self.repo.status()

if __name__ == '__main__':
    repo = Git('/home/dinever/pygit/tmp/Crotal')
    # repo = Git('/home/dinever/pygit/tmp/Crotal')
    print repo.repo.is_empty
    pprint.pprint(repo._get_refs())
    # pprint.pprint(repo.get_commit('489c871b30ff162446cc42971cb38f831bf25727'))
    # pprint.pprint(repo.diff_commits_by_cid('489c871b30ff162446cc42971cb38f831bf25727'))
    # repo.clone_repository('Crotal', 'new')
    # pprint.pprint(repo.get_file('setup.py'))
    # pprint.pprint(repo.get_status())
    pprint.pprint(repo.get_tree())
    repo.get_all_files()

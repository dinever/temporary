#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
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

    def get_commit(self, cid=''):
        refs = self._get_refs()
        ctx = {"project": self.repo}
        if cid == '':
            commit = self.repo[self.repo.head.target]
        else:
            commit = self.repo[unicode(cid)]
        ctx['commit'] = commit
        ctx['refs'] = refs

        if len(commit.parents) > 0:
            commit_b = self.repo[commit.parents[0].hex]
            diff = commit_b.tree.diff_to_tree(commit.tree)
            try:
                ctx['patch'] = diff.patch.decode('utf-8')
            except UnicodeDecodeError:
                ctx['patch'] = diff.patch
        else:
            tb = self.repo.TreeBuilder()
            diff = self.repo[tb.write()].diff(commit.tree)
        return ctx

    def diff_commits(self, commit, from_commit=None, **kwargs):
        tree = commit.tree
        from_tree = from_commit.tree if from_commit else None
        # call pygit2 diff
        if from_tree:
            diff = self.repo.diff(from_tree, tree, **kwargs)
            old_sha = from_commit.hex
        else:
            diff = tree.diff_to_tree(swap=True, **kwargs)
            old_sha = None
        return diff, old_sha


if __name__ == '__main__':
    repo = Git('/home/dinever/pygit/tmp/Crotal')
    print repo.repo.is_empty
    a = time.time()
    print repo._get_refs()
    print time.time() - a
    commit = repo.get_history('master', max_commits=20, skip=0)[11]
    commit_old = repo.get_history('master', max_commits=20, skip=0)[12]
    repo.get_commit()
    diff = repo.diff_commits(commit, commit_old)[0]
    patches = [p for p in diff]
    for p in patches:
        # print p.old_file_path
        # print p.additions
        # print p.new_file_path
        # print p.deletions
        # print p.status
        for h in p.hunks:
            print h.old_start
            print h.new_start
            print h.old_lines
            print h.new_lines
            for l in h.lines:
                print l
            print '====='

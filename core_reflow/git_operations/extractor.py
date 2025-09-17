"""
变更提取器模块
负责从Git仓库中提取MR的代码变更
"""

import git
from typing import List, Dict, Any


class ChangeExtractor:
    """Git变更提取器"""

    def __init__(self, repo_path: str):
        """
        初始化变更提取器

        Args:
            repo_path: Git仓库路径
        """
        self.repo = git.Repo(repo_path)

    def extract_changes(self, mr_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从MR信息中提取代码变更

        Args:
            mr_info: MR信息字典

        Returns:
            变更列表
        """
        try:
            # 方法1：通过merge commit获取变更
            if mr_info.get('merge_commit_sha'):
                commit = self.repo.commit(mr_info['merge_commit_sha'])
                return self._get_commit_changes(commit)

            # 方法2：通过分支对比获取变更
            return self._get_branch_diff(
                mr_info['source_branch'],
                mr_info['target_branch']
            )

        except Exception as e:
            print(f"提取变更失败: {e}")
            return []

    def _get_commit_changes(self, commit) -> List[Dict[str, Any]]:
        """
        获取提交的变更内容

        Args:
            commit: Git提交对象

        Returns:
            变更列表
        """
        try:
            if len(commit.parents) == 0:
                # 初始提交
                diff = commit.diff(create_patch=True)
            else:
                # 普通提交
                parent = commit.parents[0]
                diff = parent.diff(commit, create_patch=True)

            return self._parse_diff(diff)

        except Exception as e:
            print(f"获取提交变更失败: {e}")
            return []

    def _get_branch_diff(self, source_branch: str, target_branch: str) -> List[Dict[str, Any]]:
        """
        获取分支间的差异

        Args:
            source_branch: 源分支
            target_branch: 目标分支

        Returns:
            变更列表
        """
        try:
            # 获取分支的最新提交
            source_commit = self.repo.commit(f'origin/{source_branch}')
            target_commit = self.repo.commit(f'origin/{target_branch}')

            # 计算差异
            diff = target_commit.diff(source_commit, create_patch=True)
            return self._parse_diff(diff)

        except Exception as e:
            print(f"获取分支差异失败: {e}")
            return []

    def _parse_diff(self, diff) -> List[Dict[str, Any]]:
        """
        解析diff内容

        Args:
            diff: Git diff对象

        Returns:
            变更列表
        """
        changes = []

        for patch in diff:
            # 只处理代码文件
            if self._is_code_file(patch.a_path or patch.b_path):
                change = {
                    'file_path': patch.a_path or patch.b_path,
                    'change_type': self._detect_change_type(patch),
                    'diff_content': patch.diff.decode('utf-8', errors='ignore') if patch.diff else ''
                }
                changes.append(change)

        return changes

    def _is_code_file(self, file_path: str) -> bool:
        """
        判断是否为代码文件

        Args:
            file_path: 文件路径

        Returns:
            是否为代码文件
        """
        if not file_path:
            return False

        code_extensions = {'.py', '.java', '.js', '.ts', '.cpp', '.c', '.h', '.go', '.rs'}
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _detect_change_type(self, patch) -> str:
        """
        检测变更类型

        Args:
            patch: Git patch对象

        Returns:
            变更类型
        """
        if patch.new_file:
            return 'ADD'
        elif patch.deleted_file:
            return 'DELETE'
        else:
            return 'MODIFY'

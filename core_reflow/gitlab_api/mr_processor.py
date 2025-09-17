"""
MR处理器模块
负责从GitLab获取MR信息
"""

import gitlab
from typing import List, Dict, Any


class MRProcessor:
    """GitLab MR处理器"""

    def __init__(self, gitlab_token: str, project_id: int, gitlab_url: str = 'https://gitlab.com'):
        """
        初始化MR处理器

        Args:
            gitlab_token: GitLab访问令牌
            project_id: 项目ID
            gitlab_url: GitLab服务器地址
        """
        self.gitlab = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
        self.project = self.gitlab.projects.get(project_id)

    def get_branch_mrs(self, source_branch: str, target_branch: str = 'dev_master') -> List[Dict[str, Any]]:
        """
        获取指定分支的MR列表

        Args:
            source_branch: 源分支名称
            target_branch: 目标分支名称

        Returns:
            MR信息列表
        """
        try:
            # 获取已合并的MR
            mrs = self.project.mergerequests.list(
                source_branch=source_branch,
                target_branch=target_branch,
                state='merged',
                order_by='updated_at',
                sort='desc'
            )

            return [self._enrich_mr(mr) for mr in mrs]

        except Exception as e:
            print(f"获取MR列表失败: {e}")
            return []

    def get_mr_by_id(self, mr_id: int) -> Dict[str, Any]:
        """
        根据ID获取单个MR信息

        Args:
            mr_id: MR ID

        Returns:
            MR信息字典
        """
        try:
            mr = self.project.mergerequests.get(mr_id)
            return self._enrich_mr(mr)
        except Exception as e:
            print(f"获取MR #{mr_id} 失败: {e}")
            return {}

    def _enrich_mr(self, mr) -> Dict[str, Any]:
        """
        丰富MR信息

        Args:
            mr: GitLab MR对象

        Returns:
            包含完整信息的MR字典
        """
        return {
            'id': mr.iid,
            'title': mr.title,
            'description': mr.description or '',
            'source_branch': mr.source_branch,
            'target_branch': mr.target_branch,
            'merge_commit_sha': mr.merge_commit_sha,
            'state': mr.state,
            'author': mr.author['username'] if mr.author else 'unknown',
            'created_at': mr.created_at,
            'merged_at': mr.merged_at,
            'web_url': mr.web_url
        }

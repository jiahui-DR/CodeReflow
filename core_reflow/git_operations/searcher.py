"""
主线分支搜索器模块
负责在dev_master分支中搜索MR变更的匹配
"""

import git
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..utils.exceptions import GitOperationError, BranchNotFoundError
from ..utils.validators import validate_repo_path, validate_branch_name, validate_days_back
from ..utils.fingerprint_utils import generate_fingerprint_for_change
from ..utils.common import is_code_file, detect_change_type, safe_decode_bytes
from ..utils.cache import get_default_cache_manager, cached

logger = logging.getLogger(__name__)


class MasterBranchSearcher:
    """主线分支搜索器"""

    def __init__(self, repo_path: str, target_branch: str = 'dev_master', 
                 cache_manager=None, ignore_patterns: Optional[List[str]] = None):
        """
        初始化主线分支搜索器

        Args:
            repo_path: Git仓库路径
            target_branch: 目标分支名称
            cache_manager: 缓存管理器
            ignore_patterns: 忽略模式列表

        Raises:
            GitOperationError: Git操作失败时抛出
            BranchNotFoundError: 分支不存在时抛出
        """
        try:
            # 验证输入参数
            self.repo_path = validate_repo_path(repo_path)
            self.target_branch = validate_branch_name(target_branch)
            
            # 初始化Git仓库
            self.repo = git.Repo(self.repo_path)
            
            # 验证目标分支是否存在
            self._validate_target_branch()
            
            # 设置缓存
            self.cache_manager = cache_manager or get_default_cache_manager()
            
            # 设置忽略模式
            self.ignore_patterns = ignore_patterns
            
            logger.info(f"Initialized MasterBranchSearcher for {self.target_branch} in {self.repo_path}")
            
        except git.exc.InvalidGitRepositoryError:
            raise GitOperationError(f"Invalid Git repository: {repo_path}")
        except Exception as e:
            raise GitOperationError(f"Failed to initialize searcher: {e}")

    def _validate_target_branch(self) -> None:
        """
        验证目标分支是否存在

        Raises:
            BranchNotFoundError: 分支不存在时抛出
        """
        try:
            # 检查远程分支
            remote_branches = [ref.name for ref in self.repo.remote().refs]
            target_remote_branch = f'origin/{self.target_branch}'
            
            if target_remote_branch not in remote_branches:
                # 检查本地分支
                local_branches = [ref.name for ref in self.repo.heads]
                if self.target_branch not in local_branches:
                    raise BranchNotFoundError(self.target_branch)
                    
        except git.exc.GitCommandError:
            raise BranchNotFoundError(self.target_branch)

    def search_changes_in_master(self, mr_fingerprints: List[Dict[str, Any]], days_back: int = 30) -> List[Dict[str, Any]]:
        """
        在主线分支中搜索MR变更的匹配

        Args:
            mr_fingerprints: MR指纹列表
            days_back: 搜索时间范围（天）

        Returns:
            搜索结果列表

        Raises:
            GitOperationError: Git操作失败时抛出
        """
        try:
            # 验证输入参数
            if not isinstance(mr_fingerprints, list):
                raise GitOperationError(f"mr_fingerprints must be a list, got {type(mr_fingerprints)}")
            
            days_back = validate_days_back(days_back)
            
            # 获取主线分支最近的提交
            logger.info(f"Searching in {self.target_branch} for last {days_back} days")
            master_commits = self._get_recent_commits(days_back)
            
            if not master_commits:
                logger.warning(f"No commits found in {self.target_branch} for last {days_back} days")
                return []

            results = []
            for i, fingerprint in enumerate(mr_fingerprints):
                try:
                    match_result = self._search_fingerprint_in_commits(fingerprint, master_commits)
                    result = {
                        'mr_id': fingerprint.get('mr_id'),
                        'fingerprint': fingerprint['fingerprint'],
                        'file_path': fingerprint['file_path'],
                        'matched': match_result['matched'],
                        'match_commit': match_result.get('commit', ''),
                        'match_type': match_result.get('type', 'none'),
                        'confidence': match_result['confidence']
                    }
                    results.append(result)
                    
                    logger.debug(f"Processed fingerprint {i+1}/{len(mr_fingerprints)}: "
                               f"{'matched' if match_result['matched'] else 'no match'}")
                    
                except Exception as e:
                    logger.error(f"Failed to process fingerprint {i}: {e}")
                    # 添加失败的结果项
                    results.append({
                        'mr_id': fingerprint.get('mr_id'),
                        'fingerprint': fingerprint.get('fingerprint', ''),
                        'file_path': fingerprint.get('file_path', ''),
                        'matched': False,
                        'match_commit': '',
                        'match_type': 'error',
                        'confidence': 0.0
                    })

            logger.info(f"Search completed: {len(results)} results, "
                       f"{sum(1 for r in results if r['matched'])} matches found")
            return results

        except Exception as e:
            raise GitOperationError(f"搜索主线分支失败: {e}")

    @cached(get_default_cache_manager(), ttl=300)  # 5分钟缓存
    def _get_recent_commits(self, days_back: int) -> List:
        """
        获取主线分支最近的提交（带缓存）

        Args:
            days_back: 搜索天数

        Returns:
            提交列表

        Raises:
            GitOperationError: Git操作失败时抛出
        """
        try:
            since_date = datetime.now() - timedelta(days=days_back)

            # 获取目标分支的提交
            commits = list(self.repo.iter_commits(
                self.target_branch,
                since=since_date,
                max_count=1000  # 限制最大提交数量
            ))

            logger.debug(f"Found {len(commits)} commits in {self.target_branch} "
                        f"since {since_date.strftime('%Y-%m-%d')}")
            return commits

        except git.exc.GitCommandError as e:
            raise GitOperationError(f"获取主线分支提交失败: {e}")
        except Exception as e:
            raise GitOperationError(f"Git操作失败: {e}")

    def _search_fingerprint_in_commits(self, fingerprint: Dict[str, Any], commits: List) -> Dict[str, Any]:
        """
        在提交列表中搜索指纹匹配

        Args:
            fingerprint: 指纹信息
            commits: 提交列表

        Returns:
            匹配结果
        """
        if not commits:
            return {'matched': False, 'confidence': 0.0}

        target_fingerprint = fingerprint['fingerprint']
        file_path = fingerprint.get('file_path', '')
        
        for commit in commits:
            try:
                # 使用缓存的指纹检查
                match_result = self._check_commit_fingerprint_cached(
                    commit.hexsha, target_fingerprint, file_path
                )

                if match_result['matched']:
                    logger.debug(f"Found match in commit {commit.hexsha[:8]} for {file_path}")
                    return match_result

            except Exception as e:
                logger.warning(f"检查提交 {commit.hexsha[:8]} 失败: {e}")
                continue

        return {'matched': False, 'confidence': 0.0}

    @cached(get_default_cache_manager(), ttl=1800)  # 30分钟缓存
    def _check_commit_fingerprint_cached(self, commit_sha: str, target_fingerprint: str, 
                                       file_path: str) -> Dict[str, Any]:
        """
        检查提交指纹（带缓存）

        Args:
            commit_sha: 提交哈希
            target_fingerprint: 目标指纹
            file_path: 文件路径

        Returns:
            匹配结果
        """
        try:
            commit = self.repo.commit(commit_sha)
            return self._check_commit_fingerprint(commit, {
                'fingerprint': target_fingerprint,
                'file_path': file_path
            })
        except Exception as e:
            logger.error(f"Failed to check commit {commit_sha[:8]}: {e}")
            return {'matched': False, 'confidence': 0.0}

    def _check_commit_fingerprint(self, commit, fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查提交是否包含匹配的指纹

        Args:
            commit: Git提交对象
            fingerprint: 指纹信息

        Returns:
            匹配结果
        """
        try:
            # 获取提交的变更
            if len(commit.parents) == 0:
                # 初始提交
                diff = commit.diff(create_patch=True)
            else:
                # 普通提交
                parent = commit.parents[0]
                diff = parent.diff(commit, create_patch=True)

            # 解析提交的变更
            commit_changes = self._parse_commit_diff(diff)

            # 过滤相关文件的变更
            target_file_path = fingerprint.get('file_path', '')
            relevant_changes = []
            
            for change in commit_changes:
                if not target_file_path or change['file_path'] == target_file_path:
                    relevant_changes.append(change)

            # 生成该提交的指纹并比较
            if relevant_changes:
                for change in relevant_changes:
                    commit_fingerprint = generate_fingerprint_for_change(
                        change, self.ignore_patterns
                    )
                    
                    if (commit_fingerprint and 
                        commit_fingerprint['fingerprint'] == fingerprint['fingerprint']):
                        return {
                            'matched': True,
                            'commit': commit.hexsha,
                            'type': 'direct_match',
                            'confidence': 1.0
                        }

            return {'matched': False, 'confidence': 0.0}

        except Exception as e:
            logger.error(f"检查提交指纹失败: {e}")
            return {'matched': False, 'confidence': 0.0}

    def _parse_commit_diff(self, diff) -> List[Dict[str, Any]]:
        """
        解析提交的diff内容

        Args:
            diff: Git diff对象

        Returns:
            变更列表
        """
        changes = []

        for patch in diff:
            file_path = patch.a_path or patch.b_path
            # 只处理代码文件
            if is_code_file(file_path):
                try:
                    diff_content = safe_decode_bytes(patch.diff) if patch.diff else ''
                    change = {
                        'file_path': file_path,
                        'change_type': detect_change_type(patch),
                        'diff_content': diff_content
                    }
                    changes.append(change)
                except Exception as e:
                    logger.warning(f"Failed to parse diff for {file_path}: {e}")

        return changes

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        return self.cache_manager.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache_manager.clear()
        logger.info("Cache cleared for MasterBranchSearcher")

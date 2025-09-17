"""
交付分支验证器
自动获取交付分支的所有MR，并验证其是否进入主线分支
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..gitlab_api.mr_processor import MRProcessor
from ..git_operations.extractor import ChangeExtractor
from ..fingerprint.generator import FingerprintGenerator
from ..git_operations.searcher import MasterBranchSearcher
from .validator import MatchValidator
from ..utils.exceptions import ValidationError, GitLabAPIError, GitOperationError
from ..utils.metrics import timer_context, count_operation

logger = logging.getLogger(__name__)


class DeliveryBranchValidator:
    """交付分支MR验证器"""

    def __init__(self, repo_config: Dict[str, Any], cache_manager=None):
        """
        初始化交付分支验证器
        
        Args:
            repo_config: 仓库配置
            cache_manager: 缓存管理器
        """
        self.repo_config = repo_config
        self.repo_name = repo_config['name']
        
        # 初始化各个组件
        gitlab_config = repo_config['gitlab']
        git_config = repo_config['git']
        
        self.mr_processor = MRProcessor(
            gitlab_config['token'],
            gitlab_config['project_id'],
            gitlab_config['url']
        )
        
        self.change_extractor = ChangeExtractor(git_config['repo_path'])
        self.fingerprint_generator = FingerprintGenerator()
        
        self.master_searcher = MasterBranchSearcher(
            git_config['repo_path'],
            git_config['master_branch'],
            cache_manager=cache_manager
        )
        
        self.match_validator = MatchValidator()
        
        self.delivery_branch = git_config['delivery_branch']
        self.master_branch = git_config['master_branch']
        self.search_days = git_config.get('search_days', 90)
        
        logger.info(f"Initialized DeliveryBranchValidator for {self.repo_name}")

    def validate_delivery_branch(self) -> Dict[str, Any]:
        """
        验证交付分支的所有MR
        
        Returns:
            验证结果字典
        """
        try:
            with timer_context(f"validate_delivery_branch_{self.repo_name}"):
                logger.info(f"开始验证交付分支: {self.delivery_branch}")
                
                # 1. 获取交付分支的所有MR
                delivery_mrs = self._get_delivery_branch_mrs()
                count_operation("delivery_mrs_found", len(delivery_mrs))
                
                if not delivery_mrs:
                    logger.warning(f"交付分支 {self.delivery_branch} 未找到任何MR")
                    return self._create_empty_result()
                
                logger.info(f"找到 {len(delivery_mrs)} 个交付分支MR")
                
                # 2. 逐一验证每个MR
                validation_results = []
                
                for i, mr in enumerate(delivery_mrs, 1):
                    logger.info(f"验证进度 {i}/{len(delivery_mrs)} - MR #{mr['iid']}")
                    
                    try:
                        result = self._validate_single_mr(mr)
                        validation_results.append(result)
                        
                    except Exception as e:
                        logger.error(f"验证MR #{mr['iid']} 失败: {e}")
                        validation_results.append({
                            'mr_id': mr['iid'],
                            'title': mr.get('title', 'Unknown'),
                            'status': 'ERROR',
                            'error': str(e)
                        })
                
                # 3. 汇总结果
                summary = self._summarize_results(delivery_mrs, validation_results)
                
                logger.info(f"验证完成: {summary['merged_count']}/{summary['total_mrs']} MR已进入主线")
                
                return summary
                
        except Exception as e:
            logger.error(f"验证交付分支失败: {e}")
            raise ValidationError(f"交付分支验证失败: {e}")

    def _get_delivery_branch_mrs(self) -> List[Dict[str, Any]]:
        """获取交付分支的所有MR"""
        try:
            # 获取合并到交付分支的MR
            mrs = self.mr_processor.project.mergerequests.list(
                state='merged',
                target_branch=self.delivery_branch,
                order_by='updated_at',
                sort='desc',
                get_all=True
            )
            
            # 转换为字典格式
            mr_list = []
            for mr in mrs:
                mr_dict = {
                    'iid': mr.iid,
                    'id': mr.id,
                    'title': mr.title,
                    'source_branch': mr.source_branch,
                    'target_branch': mr.target_branch,
                    'merge_commit_sha': mr.merge_commit_sha,
                    'merged_at': mr.merged_at,
                    'author': mr.author.get('name') if mr.author else 'Unknown',
                    'web_url': mr.web_url
                }
                mr_list.append(mr_dict)
            
            return mr_list
            
        except Exception as e:
            logger.error(f"获取交付分支MR失败: {e}")
            raise GitLabAPIError(f"无法获取交付分支MR: {e}")

    def _validate_single_mr(self, mr: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个MR是否在主线分支中"""
        mr_id = mr['iid']
        
        try:
            # 1. 提取MR变更
            changes = self.change_extractor.extract_changes(mr)
            count_operation("mr_changes_extracted", len(changes) if changes else 0)
            
            if not changes:
                return {
                    'mr_id': mr_id,
                    'title': mr['title'],
                    'author': mr['author'],
                    'merged_at': mr['merged_at'],
                    'status': 'NO_CHANGES',
                    'message': '未找到代码变更',
                    'web_url': mr['web_url']
                }
            
            # 2. 生成指纹
            fingerprints = self.fingerprint_generator.generate(changes, mr_id)
            count_operation("mr_fingerprints_generated", len(fingerprints) if fingerprints else 0)
            
            if not fingerprints:
                return {
                    'mr_id': mr_id,
                    'title': mr['title'],
                    'author': mr['author'],
                    'merged_at': mr['merged_at'],
                    'status': 'NO_FINGERPRINTS',
                    'message': '未生成有效指纹（可能都是注释变更）',
                    'web_url': mr['web_url']
                }
            
            # 3. 在主线分支中搜索
            search_results = self.master_searcher.search_changes_in_master(
                fingerprints, self.search_days
            )
            
            # 4. 验证匹配结果
            validated_results = self.match_validator.validate_results(search_results)
            
            # 5. 判断是否已合并
            is_merged = self._determine_merge_status(validated_results)
            confidence = self._calculate_confidence(validated_results)
            
            count_operation("mr_validation_completed", 1)
            if is_merged:
                count_operation("mr_merged_to_master", 1)
            
            return {
                'mr_id': mr_id,
                'title': mr['title'],
                'author': mr['author'],
                'merged_at': mr['merged_at'],
                'source_branch': mr['source_branch'],
                'status': 'MERGED' if is_merged else 'NOT_MERGED',
                'confidence': confidence,
                'changes_count': len(changes),
                'fingerprints_count': len(fingerprints),
                'matches_found': len([r for r in validated_results if r.get('matched', False)]),
                'web_url': mr['web_url'],
                'details': validated_results[:3]  # 只保留前3个匹配结果
            }
            
        except Exception as e:
            logger.error(f"验证MR #{mr_id} 时出错: {e}")
            raise

    def _determine_merge_status(self, validated_results: List[Dict[str, Any]]) -> bool:
        """判断MR是否已合并到主线分支"""
        if not validated_results:
            return False
        
        # 如果有高置信度的匹配，认为已合并
        high_confidence_matches = [
            r for r in validated_results 
            if r.get('matched', False) and r.get('confidence', 0) >= 0.8
        ]
        
        return len(high_confidence_matches) > 0

    def _calculate_confidence(self, validated_results: List[Dict[str, Any]]) -> float:
        """计算整体置信度"""
        if not validated_results:
            return 0.0
        
        matched_results = [r for r in validated_results if r.get('matched', False)]
        if not matched_results:
            return 0.0
        
        # 取最高置信度
        max_confidence = max(r.get('confidence', 0) for r in matched_results)
        return max_confidence

    def _summarize_results(self, delivery_mrs: List[Dict], 
                         validation_results: List[Dict]) -> Dict[str, Any]:
        """汇总验证结果"""
        
        merged_results = [r for r in validation_results if r['status'] == 'MERGED']
        not_merged_results = [r for r in validation_results if r['status'] == 'NOT_MERGED']
        no_changes_results = [r for r in validation_results if r['status'] == 'NO_CHANGES']
        error_results = [r for r in validation_results if r['status'] == 'ERROR']
        
        return {
            'repository': self.repo_name,
            'delivery_branch': self.delivery_branch,
            'master_branch': self.master_branch,
            'search_days': self.search_days,
            'total_mrs': len(delivery_mrs),
            'merged_count': len(merged_results),
            'not_merged_count': len(not_merged_results),
            'no_changes_count': len(no_changes_results),
            'error_count': len(error_results),
            'merge_rate': len(merged_results) / len(delivery_mrs) if delivery_mrs else 0,
            'validation_timestamp': datetime.now().isoformat(),
            'results': validation_results,
            'summary': {
                'merged_mrs': merged_results,
                'not_merged_mrs': not_merged_results,
                'problematic_mrs': no_changes_results + error_results
            }
        }

    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空的验证结果"""
        return {
            'repository': self.repo_name,
            'delivery_branch': self.delivery_branch,
            'master_branch': self.master_branch,
            'total_mrs': 0,
            'merged_count': 0,
            'not_merged_count': 0,
            'no_changes_count': 0,
            'error_count': 0,
            'merge_rate': 0.0,
            'validation_timestamp': datetime.now().isoformat(),
            'results': [],
            'summary': {
                'merged_mrs': [],
                'not_merged_mrs': [],
                'problematic_mrs': []
            }
        }


class MultiRepositoryValidator:
    """多仓库验证器"""
    
    def __init__(self, repositories_config: List[Dict[str, Any]], cache_manager=None):
        """
        初始化多仓库验证器
        
        Args:
            repositories_config: 多个仓库的配置列表
            cache_manager: 缓存管理器
        """
        self.repositories_config = repositories_config
        self.cache_manager = cache_manager
        
    def validate_all_repositories(self) -> Dict[str, Any]:
        """验证所有配置的仓库"""
        results = {}
        
        for repo_config in self.repositories_config:
            repo_name = repo_config['name']
            logger.info(f"开始验证仓库: {repo_name}")
            
            try:
                validator = DeliveryBranchValidator(repo_config, self.cache_manager)
                result = validator.validate_delivery_branch()
                results[repo_name] = result
                
            except Exception as e:
                logger.error(f"验证仓库 {repo_name} 失败: {e}")
                results[repo_name] = {
                    'repository': repo_name,
                    'error': str(e),
                    'status': 'ERROR'
                }
        
        return self._create_global_summary(results)
    
    def _create_global_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """创建全局汇总"""
        successful_results = {k: v for k, v in results.items() if 'error' not in v}
        
        total_repos = len(results)
        successful_repos = len(successful_results)
        total_mrs = sum(r.get('total_mrs', 0) for r in successful_results.values())
        total_merged = sum(r.get('merged_count', 0) for r in successful_results.values())
        
        return {
            'global_summary': {
                'total_repositories': total_repos,
                'successful_repositories': successful_repos,
                'total_mrs': total_mrs,
                'total_merged': total_merged,
                'global_merge_rate': total_merged / total_mrs if total_mrs > 0 else 0,
                'validation_timestamp': datetime.now().isoformat()
            },
            'repository_results': results
        }

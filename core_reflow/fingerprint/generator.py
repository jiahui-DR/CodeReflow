"""
指纹生成器模块
负责为代码变更生成唯一指纹标识
"""

import logging
from typing import List, Dict, Any, Optional

from ..utils.fingerprint_utils import generate_fingerprint_for_change
from ..utils.exceptions import FingerprintGenerationError
from ..utils.validators import validate_file_extensions

logger = logging.getLogger(__name__)


class FingerprintGenerator:
    """代码指纹生成器"""

    def __init__(self, ignore_patterns: Optional[List[str]] = None):
        """
        初始化指纹生成器

        Args:
            ignore_patterns: 要忽略的行模式列表
        """
        self.ignore_patterns = ignore_patterns or [
            r'^\s*#.*$',         # Python注释
            r'^\s*$',             # 空行
            r'^\s*import',        # 导入语句
            r'^\s*from.*import',  # 导入语句
            r'^\s*//.*$',         # JavaScript注释
            r'^\s*/\*.*\*/$',     # 多行注释
            r'^\s*package',       # Java包声明
            r'^\s*public class',  # Java类声明
        ]

    def generate(self, changes: List[Dict[str, Any]], mr_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        为MR变更生成指纹

        Args:
            changes: 变更列表
            mr_id: MR ID

        Returns:
            指纹列表

        Raises:
            FingerprintGenerationError: 指纹生成失败时抛出
        """
        if not isinstance(changes, list):
            raise FingerprintGenerationError(f"Changes must be a list, got {type(changes)}")

        fingerprints = []
        failed_changes = []

        for i, change in enumerate(changes):
            try:
                # 验证变更数据结构
                self._validate_change_data(change)
                
                # 使用工具函数生成指纹
                fingerprint = generate_fingerprint_for_change(
                    change, self.ignore_patterns, mr_id
                )

                if fingerprint:
                    fingerprints.append(fingerprint)
                    logger.debug(f"Generated fingerprint for {change['file_path']}: {fingerprint['fingerprint']}")
                else:
                    logger.debug(f"No meaningful changes found for {change['file_path']}")

            except Exception as e:
                error_msg = f"Failed to generate fingerprint for change {i}: {change.get('file_path', 'unknown')}"
                logger.error(f"{error_msg}: {e}")
                failed_changes.append({'index': i, 'file_path': change.get('file_path'), 'error': str(e)})

        if failed_changes:
            logger.warning(f"Failed to generate fingerprints for {len(failed_changes)} changes")

        logger.info(f"Generated {len(fingerprints)} fingerprints from {len(changes)} changes")
        return fingerprints

    def _validate_change_data(self, change: Dict[str, Any]) -> None:
        """
        验证变更数据结构

        Args:
            change: 变更数据

        Raises:
            FingerprintGenerationError: 数据结构无效时抛出
        """
        required_fields = ['file_path', 'change_type', 'diff_content']
        
        if not isinstance(change, dict):
            raise FingerprintGenerationError(f"Change must be a dict, got {type(change)}")
        
        for field in required_fields:
            if field not in change:
                raise FingerprintGenerationError(f"Missing required field '{field}' in change data")
            
            if not isinstance(change[field], str):
                raise FingerprintGenerationError(f"Field '{field}' must be string, got {type(change[field])}")
        
        # 验证变更类型
        valid_change_types = {'ADD', 'DELETE', 'MODIFY'}
        if change['change_type'] not in valid_change_types:
            raise FingerprintGenerationError(f"Invalid change_type: {change['change_type']}. Valid types: {valid_change_types}")

    def compare_fingerprints(self, fp1: str, fp2: str) -> bool:
        """
        比较两个指纹是否相同

        Args:
            fp1: 指纹1
            fp2: 指纹2

        Returns:
            是否相同
        """
        if not isinstance(fp1, str) or not isinstance(fp2, str):
            return False
        return fp1 == fp2

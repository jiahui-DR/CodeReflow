"""
指纹工具模块
提供独立的指纹生成和比较功能，避免循环导入
"""

import hashlib
import re
from typing import List, Dict, Any, Optional


def extract_meaningful_lines(diff_content: str, ignore_patterns: Optional[List[str]] = None) -> List[str]:
    """
    提取有意义的变更行

    Args:
        diff_content: diff内容
        ignore_patterns: 要忽略的行模式列表

    Returns:
        有意义的变更行列表
    """
    if ignore_patterns is None:
        ignore_patterns = [
            r'^\s*#.*$',         # Python注释
            r'^\s*$',             # 空行
            r'^\s*import',        # 导入语句
            r'^\s*from.*import',  # 导入语句
            r'^\s*//.*$',         # JavaScript注释
            r'^\s*/\*.*\*/$',     # 多行注释
            r'^\s*package',       # Java包声明
            r'^\s*public class',  # Java类声明
        ]

    compiled_patterns = [re.compile(pattern) for pattern in ignore_patterns]
    lines = diff_content.split('\n')
    meaningful_lines = []

    for line in lines:
        # 跳过diff头部信息
        if line.startswith('@@') or line.startswith('+++') or line.startswith('---'):
            continue

        # 只处理变更行
        if line.startswith('+') and not line.startswith('+++'):
            # 新增行
            content = line[1:].strip()
            if content and not _is_ignored_line(content, compiled_patterns):
                meaningful_lines.append(content)
        elif line.startswith('-') and not line.startswith('---'):
            # 删除行
            content = line[1:].strip()
            if content and not _is_ignored_line(content, compiled_patterns):
                meaningful_lines.append(content)

    return meaningful_lines


def _is_ignored_line(line: str, patterns: List[re.Pattern]) -> bool:
    """
    判断是否为忽略行

    Args:
        line: 代码行
        patterns: 编译后的正则模式列表

    Returns:
        是否为忽略行
    """
    for pattern in patterns:
        if pattern.match(line):
            return True
    return False


def generate_content_fingerprint(content_lines: List[str]) -> str:
    """
    为内容行列表生成指纹

    Args:
        content_lines: 内容行列表

    Returns:
        16位指纹字符串
    """
    if not content_lines:
        return ""

    content_hash = hashlib.sha256(
        ''.join(content_lines).encode('utf-8', errors='ignore')
    ).hexdigest()[:16]

    return content_hash


def generate_fingerprint_for_change(change: Dict[str, Any], 
                                   ignore_patterns: Optional[List[str]] = None,
                                   mr_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    为单个变更生成指纹

    Args:
        change: 变更信息
        ignore_patterns: 忽略模式列表
        mr_id: MR ID

    Returns:
        指纹信息字典
    """
    # 提取有意义的变更行
    meaningful_lines = extract_meaningful_lines(change['diff_content'], ignore_patterns)

    if not meaningful_lines:
        return None

    # 生成内容哈希
    content_hash = generate_content_fingerprint(meaningful_lines)

    # 生成文件级指纹
    fingerprint = {
        'fingerprint': content_hash,
        'mr_id': mr_id,
        'file_path': change['file_path'],
        'change_type': change['change_type'],
        'line_count': len(meaningful_lines),
        'content_preview': ''.join(meaningful_lines[:3]),  # 前3行预览
        'raw_content': ''.join(meaningful_lines)  # 原始内容用于调试
    }

    return fingerprint


def compare_fingerprints(fp1: str, fp2: str) -> bool:
    """
    比较两个指纹是否相同

    Args:
        fp1: 指纹1
        fp2: 指纹2

    Returns:
        是否相同
    """
    return fp1 == fp2


def calculate_similarity(lines1: List[str], lines2: List[str]) -> float:
    """
    计算两组代码行的相似度（Jaccard相似度）

    Args:
        lines1: 代码行列表1
        lines2: 代码行列表2

    Returns:
        相似度（0.0-1.0）
    """
    if not lines1 and not lines2:
        return 1.0
    
    if not lines1 or not lines2:
        return 0.0

    set1 = set(lines1)
    set2 = set(lines2)
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

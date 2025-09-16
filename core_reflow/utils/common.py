"""
公共工具函数模块
包含项目中通用的工具函数
"""

import os
import time
from typing import List, Dict, Any, Set, Optional
from pathlib import Path

from .validators import validate_file_extensions


def is_code_file(file_path: str, code_extensions: Optional[Set[str]] = None) -> bool:
    """
    判断是否为代码文件

    Args:
        file_path: 文件路径
        code_extensions: 代码文件扩展名集合

    Returns:
        是否为代码文件
    """
    if not file_path:
        return False

    if code_extensions is None:
        code_extensions = {'.py', '.java', '.js', '.ts', '.jsx', '.tsx', 
                          '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', 
                          '.php', '.scala', '.kt', '.swift', '.cs', '.vb',
                          '.sql', '.yml', '.yaml', '.xml', '.json'}

    file_path = file_path.lower()
    return any(file_path.endswith(ext) for ext in code_extensions)


def detect_change_type(patch) -> str:
    """
    检测变更类型

    Args:
        patch: Git patch对象

    Returns:
        变更类型 ('ADD', 'DELETE', 'MODIFY')
    """
    if hasattr(patch, 'new_file') and patch.new_file:
        return 'ADD'
    elif hasattr(patch, 'deleted_file') and patch.deleted_file:
        return 'DELETE'
    else:
        return 'MODIFY'


def safe_decode_bytes(data: bytes, encoding: str = 'utf-8') -> str:
    """
    安全解码字节数据

    Args:
        data: 字节数据
        encoding: 编码格式

    Returns:
        解码后的字符串
    """
    if isinstance(data, str):
        return data
    
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return data.decode(encoding, errors='ignore')


def format_duration(seconds: float) -> str:
    """
    格式化时间长度

    Args:
        seconds: 秒数

    Returns:
        格式化的时间字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m{remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h{remaining_minutes}m"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def ensure_directory_exists(directory_path: str) -> None:
    """
    确保目录存在，不存在则创建

    Args:
        directory_path: 目录路径
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def get_file_size_mb(file_path: str) -> float:
    """
    获取文件大小（MB）

    Args:
        file_path: 文件路径

    Returns:
        文件大小（MB）
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except (OSError, IOError):
        return 0.0


def chunks(lst: List, chunk_size: int):
    """
    将列表分块

    Args:
        lst: 原始列表
        chunk_size: 块大小

    Yields:
        分块后的子列表
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换非法字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除前后空格和点
    sanitized = sanitized.strip(' .')
    # 确保不为空
    if not sanitized:
        sanitized = 'unnamed'
    return sanitized


class Timer:
    """简单的计时器类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """停止计时"""
        if self.start_time is None:
            raise ValueError("Timer not started")
        self.end_time = time.time()
    
    def elapsed(self) -> float:
        """获取已用时间"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** attempt))  # 指数退避
                        continue
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator

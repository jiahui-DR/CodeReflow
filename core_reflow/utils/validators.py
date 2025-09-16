"""
输入验证模块
提供各种输入参数的验证功能
"""

import os
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .exceptions import InvalidInputError, ConfigurationError


def validate_mr_id(mr_id: Any) -> int:
    """
    验证MR ID的有效性

    Args:
        mr_id: MR ID

    Returns:
        验证后的MR ID

    Raises:
        InvalidInputError: MR ID无效时抛出
    """
    if not isinstance(mr_id, (int, str)):
        raise InvalidInputError(f"MR ID must be int or str, got {type(mr_id)}")
    
    try:
        mr_id_int = int(mr_id)
        if mr_id_int <= 0:
            raise InvalidInputError(f"MR ID must be positive, got {mr_id_int}")
        return mr_id_int
    except ValueError:
        raise InvalidInputError(f"Invalid MR ID format: {mr_id}")


def validate_branch_name(branch_name: Any) -> str:
    """
    验证分支名称的有效性

    Args:
        branch_name: 分支名称

    Returns:
        验证后的分支名称

    Raises:
        InvalidInputError: 分支名称无效时抛出
    """
    if not isinstance(branch_name, str):
        raise InvalidInputError(f"Branch name must be string, got {type(branch_name)}")
    
    if not branch_name.strip():
        raise InvalidInputError("Branch name cannot be empty")
    
    # Git分支名称规则验证
    invalid_chars = r'[\s~^:?*\[\]\\]'
    if re.search(invalid_chars, branch_name):
        raise InvalidInputError(f"Branch name contains invalid characters: {branch_name}")
    
    if branch_name.startswith('.') or branch_name.endswith('.'):
        raise InvalidInputError(f"Branch name cannot start or end with '.': {branch_name}")
    
    return branch_name.strip()


def validate_repo_path(repo_path: Any) -> str:
    """
    验证仓库路径的有效性

    Args:
        repo_path: 仓库路径

    Returns:
        验证后的绝对路径

    Raises:
        InvalidInputError: 路径无效时抛出
    """
    if not isinstance(repo_path, (str, Path)):
        raise InvalidInputError(f"Repository path must be string or Path, got {type(repo_path)}")
    
    path = Path(repo_path).resolve()
    
    if not path.exists():
        raise InvalidInputError(f"Repository path does not exist: {path}")
    
    if not path.is_dir():
        raise InvalidInputError(f"Repository path is not a directory: {path}")
    
    # 检查是否为Git仓库
    git_dir = path / '.git'
    if not git_dir.exists():
        raise InvalidInputError(f"Path is not a Git repository: {path}")
    
    return str(path)


def validate_project_id(project_id: Any) -> int:
    """
    验证项目ID的有效性

    Args:
        project_id: 项目ID

    Returns:
        验证后的项目ID

    Raises:
        InvalidInputError: 项目ID无效时抛出
    """
    if not isinstance(project_id, (int, str)):
        raise InvalidInputError(f"Project ID must be int or str, got {type(project_id)}")
    
    try:
        project_id_int = int(project_id)
        if project_id_int <= 0:
            raise InvalidInputError(f"Project ID must be positive, got {project_id_int}")
        return project_id_int
    except ValueError:
        raise InvalidInputError(f"Invalid Project ID format: {project_id}")


def validate_gitlab_token(token: Any) -> str:
    """
    验证GitLab Token的基本格式

    Args:
        token: GitLab Token

    Returns:
        验证后的Token

    Raises:
        InvalidInputError: Token无效时抛出
    """
    if not isinstance(token, str):
        raise InvalidInputError(f"GitLab token must be string, got {type(token)}")
    
    token = token.strip()
    if not token:
        raise InvalidInputError("GitLab token cannot be empty")
    
    # 基本长度检查（GitLab token通常至少20字符）
    if len(token) < 20:
        raise InvalidInputError("GitLab token appears to be too short")
    
    return token


def validate_url(url: Any) -> str:
    """
    验证URL格式

    Args:
        url: URL字符串

    Returns:
        验证后的URL

    Raises:
        InvalidInputError: URL无效时抛出
    """
    if not isinstance(url, str):
        raise InvalidInputError(f"URL must be string, got {type(url)}")
    
    url = url.strip()
    if not url:
        raise InvalidInputError("URL cannot be empty")
    
    # 简单的URL格式验证
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        raise InvalidInputError(f"Invalid URL format: {url}")
    
    return url


def validate_days_back(days: Any) -> int:
    """
    验证搜索天数参数

    Args:
        days: 天数

    Returns:
        验证后的天数

    Raises:
        InvalidInputError: 天数无效时抛出
    """
    if not isinstance(days, (int, str)):
        raise InvalidInputError(f"Days must be int or str, got {type(days)}")
    
    try:
        days_int = int(days)
        if days_int <= 0:
            raise InvalidInputError(f"Days must be positive, got {days_int}")
        if days_int > 365:
            raise InvalidInputError(f"Days cannot exceed 365, got {days_int}")
        return days_int
    except ValueError:
        raise InvalidInputError(f"Invalid days format: {days}")


def validate_output_format(output_format: Any) -> str:
    """
    验证输出格式参数

    Args:
        output_format: 输出格式

    Returns:
        验证后的输出格式

    Raises:
        InvalidInputError: 格式无效时抛出
    """
    if not isinstance(output_format, str):
        raise InvalidInputError(f"Output format must be string, got {type(output_format)}")
    
    valid_formats = {'console', 'json', 'markdown'}
    output_format = output_format.lower().strip()
    
    if output_format not in valid_formats:
        raise InvalidInputError(f"Invalid output format: {output_format}. Valid formats: {valid_formats}")
    
    return output_format


def validate_config_dict(config: Dict[str, Any]) -> None:
    """
    验证配置字典的完整性

    Args:
        config: 配置字典

    Raises:
        ConfigurationError: 配置无效时抛出
    """
    if not isinstance(config, dict):
        raise ConfigurationError(f"Config must be dict, got {type(config)}")
    
    # 必需的配置项
    required_sections = {
        'gitlab': ['url', 'token', 'project_id'],
        'git': ['repo_path', 'target_branch'],
    }
    
    for section, required_keys in required_sections.items():
        if section not in config:
            raise ConfigurationError(f"Missing required config section: {section}")
        
        section_config = config[section]
        if not isinstance(section_config, dict):
            raise ConfigurationError(f"Config section '{section}' must be dict, got {type(section_config)}")
        
        for key in required_keys:
            if key not in section_config or not section_config[key]:
                raise ConfigurationError(f"Missing required config: {section}.{key}")


def validate_file_extensions(extensions: Any) -> List[str]:
    """
    验证文件扩展名列表

    Args:
        extensions: 扩展名列表或集合

    Returns:
        验证后的扩展名列表

    Raises:
        InvalidInputError: 扩展名无效时抛出
    """
    if not isinstance(extensions, (list, set, tuple)):
        raise InvalidInputError(f"Extensions must be list, set or tuple, got {type(extensions)}")
    
    validated_extensions = []
    for ext in extensions:
        if not isinstance(ext, str):
            raise InvalidInputError(f"Extension must be string, got {type(ext)}")
        
        ext = ext.strip()
        if not ext:
            continue
            
        # 确保扩展名以点开头
        if not ext.startswith('.'):
            ext = '.' + ext
            
        # 验证扩展名格式
        if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
            raise InvalidInputError(f"Invalid extension format: {ext}")
            
        validated_extensions.append(ext)
    
    return validated_extensions

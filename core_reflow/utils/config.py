"""
配置管理模块
负责加载和管理配置文件
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .exceptions import ConfigurationError
from .validators import validate_config_dict, validate_file_extensions

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径

        Raises:
            ConfigurationError: 配置加载失败时抛出
        """
        try:
            if config_file is None:
                config_file = self._find_config_file()

            self.config_file = config_file
            self.config = self._load_config()
            
            # 加载后立即验证配置
            if self.config:
                self._validate_loaded_config()
                
            logger.info(f"Configuration loaded from: {self.config_file}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize config manager: {e}")

    def _find_config_file(self) -> str:
        """
        查找配置文件

        Returns:
            配置文件路径
        """
        # 当前目录查找
        current_dir = Path.cwd()
        config_files = ['config.json', 'config.example.json']

        for config_file in config_files:
            if (current_dir / config_file).exists():
                return str(current_dir / config_file)

        # 默认返回当前目录的config.json
        return str(current_dir / 'config.json')

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            ConfigurationError: 配置加载失败时抛出
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.debug(f"Loaded config from {self.config_file}")
                    return config
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return self._get_default_config()
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置文件JSON格式错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            "gitlab": {
                "url": "https://gitlab.com",
                "token": "",
                "project_id": 0
            },
            "git": {
                "repo_path": ".",
                "target_branch": "dev_master",
                "search_days": 30
            },
            "fingerprint": {
                "ignore_patterns": [
                    "^\\s*#.*$",
                    "^\\s*$",
                    "^\\s*import",
                    "^\\s*from.*import"
                ]
            },
            "output": {
                "format": "console",
                "verbose": False
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔，如 'gitlab.token'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def save(self, file_path: str = None) -> bool:
        """
        保存配置到文件

        Args:
            file_path: 保存路径（可选）

        Returns:
            保存是否成功
        """
        if file_path is None:
            file_path = self.config_file

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def _validate_loaded_config(self) -> None:
        """
        验证加载的配置

        Raises:
            ConfigurationError: 配置无效时抛出
        """
        try:
            validate_config_dict(self.config)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")

    def validate(self) -> bool:
        """
        验证配置是否有效（向后兼容的方法）

        Returns:
            配置是否有效
        """
        try:
            self._validate_loaded_config()
            return True
        except ConfigurationError as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_code_extensions(self) -> set:
        """
        获取代码文件扩展名集合

        Returns:
            代码文件扩展名集合
        """
        extensions = self.get('fingerprint.code_extensions', [
            '.py', '.java', '.js', '.ts', '.jsx', '.tsx',
            '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb',
            '.php', '.scala', '.kt', '.swift', '.cs', '.vb',
            '.sql', '.yml', '.yaml', '.xml', '.json'
        ])
        
        try:
            validated_extensions = validate_file_extensions(extensions)
            return set(validated_extensions)
        except Exception as e:
            logger.warning(f"Invalid code extensions in config, using defaults: {e}")
            return {'.py', '.java', '.js', '.ts', '.cpp', '.c', '.h', '.go', '.rs'}

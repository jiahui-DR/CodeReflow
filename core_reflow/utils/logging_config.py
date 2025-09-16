"""
日志配置模块
提供结构化的日志配置和管理
"""

import logging
import logging.handlers
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class LoggingConfig:
    """日志配置管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志配置

        Args:
            config: 日志配置字典
        """
        self.config = config or {}
        self._configured = False

    def setup_logging(self) -> None:
        """设置日志配置"""
        if self._configured:
            return

        # 获取配置参数
        log_level = self.config.get('level', 'INFO').upper()
        log_format = self.config.get('format', 
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = self.config.get('file')
        max_file_size = self.config.get('max_file_size', 10 * 1024 * 1024)  # 10MB
        backup_count = self.config.get('backup_count', 5)

        # 创建根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 创建格式器
        formatter = logging.Formatter(log_format)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # 文件处理器（如果配置了文件路径）
        if log_file:
            try:
                # 确保日志目录存在
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                # 使用旋转文件处理器
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, log_level, logging.INFO))
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

            except Exception as e:
                print(f"Failed to setup file logging: {e}")

        # 设置特定模块的日志级别
        self._setup_module_loggers()

        self._configured = True
        logging.info("Logging configuration initialized")

    def _setup_module_loggers(self) -> None:
        """设置特定模块的日志级别"""
        # 设置第三方库的日志级别
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('git').setLevel(logging.WARNING)
        logging.getLogger('gitlab').setLevel(logging.INFO)

        # 设置项目模块的日志级别
        project_loggers = [
            'core_reflow.gitlab',
            'core_reflow.git',
            'core_reflow.fingerprint',
            'core_reflow.core',
            'core_reflow.utils'
        ]

        for logger_name in project_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG if self.config.get('level') == 'DEBUG' else logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器

        Args:
            name: 日志器名称

        Returns:
            日志器实例
        """
        if not self._configured:
            self.setup_logging()

        return logging.getLogger(name)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, logger: logging.Logger):
        """
        初始化结构化日志器

        Args:
            logger: 标准日志器
        """
        self.logger = logger

    def log_operation(self, operation: str, **kwargs) -> None:
        """
        记录操作日志

        Args:
            operation: 操作名称
            **kwargs: 额外的日志信息
        """
        extra_info = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"OPERATION: {operation} | {extra_info}")

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """
        记录性能日志

        Args:
            operation: 操作名称
            duration: 耗时（秒）
            **kwargs: 额外信息
        """
        extra_info = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"PERFORMANCE: {operation} | duration={duration:.3f}s | {extra_info}")

    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """
        记录错误日志

        Args:
            operation: 操作名称
            error: 异常对象
            **kwargs: 额外信息
        """
        extra_info = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.error(f"ERROR: {operation} | error={type(error).__name__}: {error} | {extra_info}")

    def log_validation(self, field: str, value: Any, status: str, **kwargs) -> None:
        """
        记录验证日志

        Args:
            field: 字段名称
            value: 字段值
            status: 验证状态 (success/failed)
            **kwargs: 额外信息
        """
        extra_info = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
        level = logging.INFO if status == 'success' else logging.WARNING
        self.logger.log(level, f"VALIDATION: {field}={value} | status={status} | {extra_info}")

    def log_cache_operation(self, operation: str, key: str, hit: bool = None, **kwargs) -> None:
        """
        记录缓存操作日志

        Args:
            operation: 操作类型 (get/set/delete/clear)
            key: 缓存键
            hit: 是否命中（仅对get操作有效）
            **kwargs: 额外信息
        """
        extra_info = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
        hit_info = f" | hit={hit}" if hit is not None else ""
        self.logger.debug(f"CACHE: {operation} | key={key}{hit_info} | {extra_info}")


# 全局日志配置实例
_logging_config = None


def setup_global_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    设置全局日志配置

    Args:
        config: 日志配置字典
    """
    global _logging_config
    _logging_config = LoggingConfig(config)
    _logging_config.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
        _logging_config.setup_logging()

    return _logging_config.get_logger(name)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    获取结构化日志器

    Args:
        name: 日志器名称

    Returns:
        结构化日志器实例
    """
    logger = get_logger(name)
    return StructuredLogger(logger)

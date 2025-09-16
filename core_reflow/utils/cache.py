"""
缓存模块
提供多种缓存实现以提升系统性能
"""

import hashlib
import logging
import pickle
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, Optional, Union, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """缓存后端抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存项"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存项是否存在"""
        pass


class MemoryCache(CacheBackend):
    """内存缓存实现"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存项数量
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None

        cache_item = self._cache[key]
        
        # 检查是否过期
        if cache_item['expires_at'] and time.time() > cache_item['expires_at']:
            self.delete(key)
            return None

        # 更新访问时间
        self._access_times[key] = time.time()
        return cache_item['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        # 如果缓存已满，移除最久未访问的项
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None

        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': expires_at
        }
        self._access_times[key] = time.time()

    def delete(self, key: str) -> None:
        """删除缓存项"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._access_times.clear()

    def exists(self, key: str) -> bool:
        """检查缓存项是否存在"""
        return self.get(key) is not None

    def _evict_lru(self) -> None:
        """移除最久未访问的缓存项"""
        if not self._access_times:
            return

        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self.delete(lru_key)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        now = time.time()
        active_items = 0
        expired_items = 0

        for cache_item in self._cache.values():
            if cache_item['expires_at'] and now > cache_item['expires_at']:
                expired_items += 1
            else:
                active_items += 1

        return {
            'total_items': len(self._cache),
            'active_items': active_items,
            'expired_items': expired_items,
            'max_size': self.max_size
        }


class FileCache(CacheBackend):
    """文件系统缓存实现"""

    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        """
        初始化文件缓存

        Args:
            cache_dir: 缓存目录
            default_ttl: 默认TTL（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用MD5哈希避免文件名问题
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed_key}.cache"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'rb') as f:
                cache_data = pickle.load(f)

            # 检查是否过期
            if cache_data['expires_at'] and time.time() > cache_data['expires_at']:
                file_path.unlink(missing_ok=True)
                return None

            return cache_data['value']

        except (pickle.PickleError, EOFError, OSError) as e:
            logger.warning(f"Failed to load cache file {file_path}: {e}")
            file_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        file_path = self._get_file_path(key)
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None

        cache_data = {
            'value': value,
            'created_at': time.time(),
            'expires_at': expires_at
        }

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except (pickle.PickleError, OSError) as e:
            logger.error(f"Failed to save cache file {file_path}: {e}")

    def delete(self, key: str) -> None:
        """删除缓存项"""
        file_path = self._get_file_path(key)
        file_path.unlink(missing_ok=True)

    def clear(self) -> None:
        """清空所有缓存"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        """检查缓存项是否存在"""
        return self.get(key) is not None


class CacheManager:
    """缓存管理器"""

    def __init__(self, backend: CacheBackend):
        """
        初始化缓存管理器

        Args:
            backend: 缓存后端实现
        """
        self.backend = backend
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        value = self.backend.get(key)
        if value is not None:
            self._hits += 1
        else:
            self._misses += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        self.backend.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """删除缓存项"""
        self.backend.delete(key)

    def clear(self) -> None:
        """清空所有缓存"""
        self.backend.clear()

    def exists(self, key: str) -> bool:
        """检查缓存项是否存在"""
        return self.backend.exists(key)

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self.get_hit_rate()
        }
        
        # 如果后端支持，添加后端统计信息
        if hasattr(self.backend, 'get_stats'):
            backend_stats = self.backend.get_stats()
            # 避免覆盖我们自己的统计信息
            for key, value in backend_stats.items():
                if key not in stats:
                    stats[key] = value
            
        return stats


def cached(cache_manager: CacheManager, ttl: Optional[int] = None, 
          key_func: Optional[Callable] = None):
    """
    缓存装饰器

    Args:
        cache_manager: 缓存管理器
        ttl: 缓存TTL（秒）
        key_func: 自定义键生成函数

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for key: {cache_key}, result cached")
            
            return result

        # 添加缓存控制方法
        wrapper.cache_clear = lambda: cache_manager.clear()
        wrapper.cache_delete = lambda *args, **kwargs: cache_manager.delete(
            key_func(*args, **kwargs) if key_func else _generate_cache_key(func.__name__, args, kwargs)
        )
        
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    生成缓存键

    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    # 简化参数表示
    simplified_args = []
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            simplified_args.append(str(arg))
        else:
            simplified_args.append(type(arg).__name__)

    simplified_kwargs = {k: str(v) if isinstance(v, (str, int, float, bool)) else type(v).__name__ 
                        for k, v in kwargs.items()}

    key_data = f"{func_name}:{simplified_args}:{simplified_kwargs}"
    return hashlib.md5(key_data.encode()).hexdigest()


# 全局缓存实例
_default_cache_manager = None


def get_default_cache_manager() -> CacheManager:
    """获取默认缓存管理器"""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager(MemoryCache())
    return _default_cache_manager


def set_default_cache_manager(cache_manager: CacheManager) -> None:
    """设置默认缓存管理器"""
    global _default_cache_manager
    _default_cache_manager = cache_manager

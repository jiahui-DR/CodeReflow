"""
缓存模块测试
"""

import unittest
import time
import tempfile
import os
from pathlib import Path

from core_reflow.utils.cache import (
    MemoryCache,
    FileCache,
    CacheManager,
    cached,
    get_default_cache_manager
)


class TestMemoryCache(unittest.TestCase):
    """内存缓存测试类"""

    def setUp(self):
        """设置测试环境"""
        self.cache = MemoryCache(max_size=3, default_ttl=1)

    def test_basic_operations(self):
        """测试基本操作"""
        # 设置和获取
        self.cache.set('key1', 'value1')
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # 检查存在性
        self.assertTrue(self.cache.exists('key1'))
        self.assertFalse(self.cache.exists('nonexistent'))
        
        # 删除
        self.cache.delete('key1')
        self.assertIsNone(self.cache.get('key1'))

    def test_ttl_expiration(self):
        """测试TTL过期"""
        self.cache.set('key1', 'value1', ttl=1)
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # 等待过期
        time.sleep(1.1)
        self.assertIsNone(self.cache.get('key1'))

    def test_lru_eviction(self):
        """测试LRU淘汰"""
        # 填满缓存
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        self.cache.set('key3', 'value3')
        
        # 访问key1使其成为最近使用
        self.cache.get('key1')
        
        # 添加新项，应该淘汰key2
        self.cache.set('key4', 'value4')
        
        self.assertIsNotNone(self.cache.get('key1'))
        self.assertIsNone(self.cache.get('key2'))
        self.assertIsNotNone(self.cache.get('key3'))
        self.assertIsNotNone(self.cache.get('key4'))

    def test_clear(self):
        """测试清空缓存"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        self.cache.clear()
        
        self.assertIsNone(self.cache.get('key1'))
        self.assertIsNone(self.cache.get('key2'))


class TestFileCache(unittest.TestCase):
    """文件缓存测试类"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = FileCache(cache_dir=self.temp_dir, default_ttl=1)

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_operations(self):
        """测试基本操作"""
        # 设置和获取
        self.cache.set('key1', 'value1')
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # 检查存在性
        self.assertTrue(self.cache.exists('key1'))
        
        # 删除
        self.cache.delete('key1')
        self.assertIsNone(self.cache.get('key1'))

    def test_ttl_expiration(self):
        """测试TTL过期"""
        self.cache.set('key1', 'value1', ttl=1)
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # 等待过期
        time.sleep(1.1)
        self.assertIsNone(self.cache.get('key1'))

    def test_persistence(self):
        """测试持久化"""
        # 设置值
        self.cache.set('key1', 'value1')
        
        # 创建新的缓存实例（模拟重启）
        new_cache = FileCache(cache_dir=self.temp_dir)
        self.assertEqual(new_cache.get('key1'), 'value1')

    def test_clear(self):
        """测试清空缓存"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        self.cache.clear()
        
        self.assertIsNone(self.cache.get('key1'))
        self.assertIsNone(self.cache.get('key2'))


class TestCacheManager(unittest.TestCase):
    """缓存管理器测试类"""

    def setUp(self):
        """设置测试环境"""
        backend = MemoryCache(max_size=10)
        self.cache_manager = CacheManager(backend)

    def test_hit_rate_tracking(self):
        """测试命中率跟踪"""
        # 初始命中率应该为0
        self.assertEqual(self.cache_manager.get_hit_rate(), 0.0)
        
        # 设置一个值
        self.cache_manager.set('key1', 'value1')
        
        # 命中
        self.cache_manager.get('key1')
        
        # 未命中
        self.cache_manager.get('nonexistent')
        
        # 命中率应该是50%
        self.assertEqual(self.cache_manager.get_hit_rate(), 0.5)

    def test_stats(self):
        """测试统计信息"""
        # 重置统计
        self.cache_manager._hits = 0
        self.cache_manager._misses = 0
        
        self.cache_manager.set('key1', 'value1')
        self.cache_manager.get('key1')  # 命中
        self.cache_manager.get('nonexistent')  # 未命中
        
        stats = self.cache_manager.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['hit_rate'], 0.5)


class TestCachedDecorator(unittest.TestCase):
    """缓存装饰器测试类"""

    def setUp(self):
        """设置测试环境"""
        self.cache_manager = CacheManager(MemoryCache())
        self.call_count = 0

    def test_function_caching(self):
        """测试函数缓存"""
        @cached(self.cache_manager, ttl=60)
        def expensive_function(x):
            self.call_count += 1
            return x * 2

        # 第一次调用
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(self.call_count, 1)

        # 第二次调用（应该从缓存获取）
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(self.call_count, 1)  # 调用次数不变

        # 不同参数的调用
        result3 = expensive_function(6)
        self.assertEqual(result3, 12)
        self.assertEqual(self.call_count, 2)

    def test_cache_clear(self):
        """测试缓存清空"""
        @cached(self.cache_manager)
        def test_function(x):
            self.call_count += 1
            return x

        # 调用函数
        test_function(1)
        self.assertEqual(self.call_count, 1)

        # 再次调用（从缓存获取）
        test_function(1)
        self.assertEqual(self.call_count, 1)

        # 清空缓存
        test_function.cache_clear()

        # 再次调用（重新执行）
        test_function(1)
        self.assertEqual(self.call_count, 2)


if __name__ == '__main__':
    unittest.main()

"""
性能指标收集模块
提供系统性能监控和指标收集功能
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from functools import wraps

from .logging_config import get_structured_logger


@dataclass
class MetricData:
    """指标数据类"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """性能统计数据"""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    success_count: int = 0
    error_count: int = 0


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_history: int = 1000):
        """
        初始化指标收集器

        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._lock = threading.Lock()
        self.logger = get_structured_logger(__name__)

    def counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        记录计数器指标

        Args:
            name: 指标名称
            value: 计数值
            tags: 标签
        """
        with self._lock:
            self._counters[name] += value
            self._add_metric(name, value, tags or {})

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        记录量表指标

        Args:
            name: 指标名称
            value: 指标值
            tags: 标签
        """
        with self._lock:
            self._gauges[name] = value
            self._add_metric(name, value, tags or {})

    def timer(self, name: str, duration: float, success: bool = True, 
             tags: Optional[Dict[str, str]] = None) -> None:
        """
        记录计时器指标

        Args:
            name: 指标名称
            duration: 耗时（秒）
            success: 是否成功
            tags: 标签
        """
        with self._lock:
            stats = self._timers[name]
            stats.count += 1
            stats.total_time += duration
            stats.min_time = min(stats.min_time, duration)
            stats.max_time = max(stats.max_time, duration)
            stats.avg_time = stats.total_time / stats.count

            if success:
                stats.success_count += 1
            else:
                stats.error_count += 1

            self._add_metric(name, duration, tags or {})

    def _add_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        """添加指标到历史记录"""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags
        )
        self._metrics[name].append(metric)

    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """获取量表值"""
        return self._gauges.get(name, 0.0)

    def get_timer_stats(self, name: str) -> PerformanceStats:
        """获取计时器统计"""
        return self._timers.get(name, PerformanceStats())

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'timers': {name: {
                    'count': stats.count,
                    'total_time': stats.total_time,
                    'avg_time': stats.avg_time,
                    'min_time': stats.min_time if stats.min_time != float('inf') else 0,
                    'max_time': stats.max_time,
                    'success_rate': stats.success_count / max(stats.count, 1),
                    'error_rate': stats.error_count / max(stats.count, 1)
                } for name, stats in self._timers.items()}
            }

    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()

    def export_metrics(self, format_type: str = 'json') -> str:
        """
        导出指标

        Args:
            format_type: 导出格式 ('json', 'prometheus')

        Returns:
            格式化的指标字符串
        """
        metrics = self.get_all_metrics()

        if format_type == 'json':
            import json
            return json.dumps(metrics, indent=2)
        elif format_type == 'prometheus':
            return self._export_prometheus_format(metrics)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _export_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """导出Prometheus格式的指标"""
        lines = []

        # 计数器
        for name, value in metrics['counters'].items():
            lines.append(f"# TYPE {name}_total counter")
            lines.append(f"{name}_total {value}")

        # 量表
        for name, value in metrics['gauges'].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        # 计时器
        for name, stats in metrics['timers'].items():
            lines.append(f"# TYPE {name}_duration_seconds histogram")
            lines.append(f"{name}_duration_seconds_count {stats['count']}")
            lines.append(f"{name}_duration_seconds_sum {stats['total_time']}")
            lines.append(f"{name}_duration_seconds_avg {stats['avg_time']}")
            lines.append(f"{name}_duration_seconds_min {stats['min_time']}")
            lines.append(f"{name}_duration_seconds_max {stats['max_time']}")
            lines.append(f"{name}_success_rate {stats['success_rate']}")
            lines.append(f"{name}_error_rate {stats['error_rate']}")

        return '\n'.join(lines)


class PerformanceTimer:
    """性能计时器上下文管理器"""

    def __init__(self, metrics_collector: MetricsCollector, name: str, 
                 tags: Optional[Dict[str, str]] = None):
        """
        初始化性能计时器

        Args:
            metrics_collector: 指标收集器
            name: 指标名称
            tags: 标签
        """
        self.metrics_collector = metrics_collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None
        self.success = True

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.success = exc_type is None
            self.metrics_collector.timer(self.name, duration, self.success, self.tags)

    def mark_error(self):
        """标记为错误"""
        self.success = False


def timed(metrics_collector: MetricsCollector, name: Optional[str] = None, 
         tags: Optional[Dict[str, str]] = None):
    """
    计时装饰器

    Args:
        metrics_collector: 指标收集器
        name: 指标名称（默认使用函数名）
        tags: 标签

    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        metric_name = name or f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTimer(metrics_collector, metric_name, tags):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def counted(metrics_collector: MetricsCollector, name: Optional[str] = None, 
           tags: Optional[Dict[str, str]] = None):
    """
    计数装饰器

    Args:
        metrics_collector: 指标收集器
        name: 指标名称（默认使用函数名）
        tags: 标签

    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        metric_name = name or f"{func.__module__}.{func.__qualname__}_calls"

        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics_collector.counter(metric_name, 1, tags)
            return func(*args, **kwargs)

        return wrapper
    return decorator


# 全局指标收集器
_global_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """设置全局指标收集器"""
    global _global_metrics_collector
    _global_metrics_collector = collector


class SystemMetrics:
    """系统指标收集器"""

    def __init__(self, metrics_collector: MetricsCollector):
        """
        初始化系统指标收集器

        Args:
            metrics_collector: 指标收集器
        """
        self.metrics_collector = metrics_collector

    def collect_system_metrics(self) -> None:
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.gauge('system.cpu.usage_percent', cpu_percent)

            # 内存使用情况
            memory = psutil.virtual_memory()
            self.metrics_collector.gauge('system.memory.usage_percent', memory.percent)
            self.metrics_collector.gauge('system.memory.available_gb', memory.available / (1024**3))
            self.metrics_collector.gauge('system.memory.used_gb', memory.used / (1024**3))

            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            self.metrics_collector.gauge('system.disk.usage_percent', 
                                       (disk.used / disk.total) * 100)
            self.metrics_collector.gauge('system.disk.free_gb', disk.free / (1024**3))

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            # Log error but don't fail
            logger = get_structured_logger(__name__)
            logger.log_error('collect_system_metrics', e)


# 便捷函数
def timer_context(name: str, tags: Optional[Dict[str, str]] = None) -> PerformanceTimer:
    """创建计时器上下文"""
    return PerformanceTimer(get_metrics_collector(), name, tags)


def count_operation(name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
    """记录操作计数"""
    get_metrics_collector().counter(name, value, tags)


def record_gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """记录量表值"""
    get_metrics_collector().gauge(name, value, tags)

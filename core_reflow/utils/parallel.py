"""
并行处理模块
提供多线程和多进程处理能力
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Union, Iterable
from functools import partial

from .logging_config import get_structured_logger
from .metrics import timer_context, count_operation


logger = get_structured_logger(__name__)


class ParallelProcessor:
    """并行处理器"""

    def __init__(self, max_workers: int = 4, executor_type: str = 'thread'):
        """
        初始化并行处理器

        Args:
            max_workers: 最大工作线程数
            executor_type: 执行器类型 ('thread' 或 'process')
        """
        self.max_workers = max_workers
        self.executor_type = executor_type.lower()
        
        if self.executor_type == 'thread':
            self.executor_class = ThreadPoolExecutor
        elif self.executor_type == 'process':
            self.executor_class = ProcessPoolExecutor
        else:
            raise ValueError(f"Unsupported executor type: {executor_type}")
            
        logger.logger.info(f"Initialized ParallelProcessor with {max_workers} {executor_type} workers")

    def map(self, func: Callable, items: Iterable, 
           chunk_size: Optional[int] = None, 
           progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        并行映射处理

        Args:
            func: 处理函数
            items: 待处理项目列表
            chunk_size: 分块大小（仅对进程池有效）
            progress_callback: 进度回调函数

        Returns:
            处理结果列表
        """
        items_list = list(items)
        if not items_list:
            return []

        with timer_context(f"parallel_map_{func.__name__}"):
            count_operation("parallel_map_tasks", len(items_list))
            
            with self.executor_class(max_workers=self.max_workers) as executor:
                if self.executor_type == 'process' and chunk_size:
                    # 进程池使用分块处理
                    results = list(executor.map(func, items_list, chunksize=chunk_size))
                else:
                    # 线程池或无分块的进程池
                    future_to_item = {executor.submit(func, item): item for item in items_list}
                    results = [None] * len(items_list)
                    
                    completed_count = 0
                    for future in as_completed(future_to_item):
                        item = future_to_item[future]
                        item_index = items_list.index(item)
                        
                        try:
                            result = future.result()
                            results[item_index] = result
                            completed_count += 1
                            
                            # 调用进度回调
                            if progress_callback:
                                progress_callback(completed_count, len(items_list), item)
                                
                            logger.logger.debug(f"Completed processing item {completed_count}/{len(items_list)}")
                            
                        except Exception as e:
                            logger.log_error(f"parallel_map_{func.__name__}", e, 
                                           item=str(item), index=item_index)
                            results[item_index] = None
                            completed_count += 1

        return results

    def map_with_error_handling(self, func: Callable, items: Iterable,
                               error_handler: Optional[Callable] = None,
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        带错误处理的并行映射

        Args:
            func: 处理函数
            items: 待处理项目列表
            error_handler: 错误处理函数
            progress_callback: 进度回调函数

        Returns:
            包含成功结果和错误信息的字典
        """
        items_list = list(items)
        if not items_list:
            return {'results': [], 'errors': [], 'success_count': 0, 'error_count': 0}

        results = []
        errors = []
        
        def safe_func(item):
            try:
                return {'success': True, 'result': func(item), 'item': item}
            except Exception as e:
                error_info = {'success': False, 'error': e, 'item': item}
                if error_handler:
                    try:
                        handled_result = error_handler(e, item)
                        error_info['handled_result'] = handled_result
                    except Exception as handler_error:
                        error_info['handler_error'] = handler_error
                return error_info

        with timer_context(f"parallel_map_safe_{func.__name__}"):
            count_operation("parallel_map_safe_tasks", len(items_list))
            
            with self.executor_class(max_workers=self.max_workers) as executor:
                future_to_item = {executor.submit(safe_func, item): item for item in items_list}
                
                completed_count = 0
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        completed_count += 1
                        
                        if result['success']:
                            results.append(result['result'])
                        else:
                            errors.append({
                                'item': result['item'],
                                'error': result['error'],
                                'handled_result': result.get('handled_result'),
                                'handler_error': result.get('handler_error')
                            })
                        
                        # 调用进度回调
                        if progress_callback:
                            progress_callback(completed_count, len(items_list), result['item'])
                            
                    except Exception as e:
                        logger.log_error("parallel_map_safe_future", e)
                        errors.append({'item': 'unknown', 'error': e})
                        completed_count += 1

        return {
            'results': results,
            'errors': errors,
            'success_count': len(results),
            'error_count': len(errors),
            'total_count': len(items_list)
        }

    def batch_process(self, func: Callable, items: Iterable, batch_size: int,
                     progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        批量处理

        Args:
            func: 批处理函数（接受一个批次的项目列表）
            items: 待处理项目列表
            batch_size: 批次大小
            progress_callback: 进度回调函数

        Returns:
            处理结果列表
        """
        items_list = list(items)
        if not items_list:
            return []

        # 创建批次
        batches = [items_list[i:i + batch_size] 
                  for i in range(0, len(items_list), batch_size)]

        with timer_context(f"parallel_batch_{func.__name__}"):
            count_operation("parallel_batch_count", len(batches))
            count_operation("parallel_batch_items", len(items_list))
            
            with self.executor_class(max_workers=self.max_workers) as executor:
                future_to_batch = {executor.submit(func, batch): batch for batch in batches}
                results = []
                
                completed_batches = 0
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    
                    try:
                        batch_result = future.result()
                        if isinstance(batch_result, list):
                            results.extend(batch_result)
                        else:
                            results.append(batch_result)
                            
                        completed_batches += 1
                        
                        # 调用进度回调
                        if progress_callback:
                            progress_callback(completed_batches, len(batches), batch)
                            
                        logger.logger.debug(f"Completed batch {completed_batches}/{len(batches)}")
                        
                    except Exception as e:
                        logger.log_error(f"parallel_batch_{func.__name__}", e, 
                                       batch_size=len(batch), batch_index=completed_batches)
                        completed_batches += 1

        return results


class MRParallelProcessor:
    """MR专用并行处理器"""

    def __init__(self, max_workers: int = 4):
        """
        初始化MR并行处理器

        Args:
            max_workers: 最大工作线程数
        """
        self.processor = ParallelProcessor(max_workers, 'thread')
        self.logger = get_structured_logger(__name__)

    def process_mrs_parallel(self, mrs: List[Dict[str, Any]], 
                           processing_func: Callable,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        并行处理MR列表

        Args:
            mrs: MR信息列表
            processing_func: MR处理函数
            progress_callback: 进度回调函数

        Returns:
            处理结果字典
        """
        if not mrs:
            return {'results': [], 'errors': [], 'success_count': 0, 'error_count': 0}

        self.logger.logger.info(f"Starting parallel processing of {len(mrs)} MRs")
        
        def mr_error_handler(error: Exception, mr: Dict[str, Any]) -> Dict[str, Any]:
            """MR处理错误处理器"""
            return {
                'mr_id': mr.get('id', 'unknown'),
                'file_path': 'error',
                'matched': False,
                'match_commit': '',
                'match_type': 'error',
                'confidence': 0.0,
                'error': str(error)
            }

        def mr_progress_callback(completed: int, total: int, mr: Dict[str, Any]):
            """MR处理进度回调"""
            mr_id = mr.get('id', 'unknown')
            self.logger.logger.info(f"Processed MR #{mr_id} ({completed}/{total})")
            
            if progress_callback:
                progress_callback(completed, total, mr)

        # 使用错误处理的并行映射
        result = self.processor.map_with_error_handling(
            processing_func,
            mrs,
            error_handler=mr_error_handler,
            progress_callback=mr_progress_callback
        )

        self.logger.logger.info(f"Parallel processing completed: "
                               f"{result['success_count']} success, "
                               f"{result['error_count']} errors")

        return result

    def process_fingerprints_parallel(self, fingerprints: List[Dict[str, Any]],
                                    search_func: Callable,
                                    batch_size: int = 10,
                                    progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        并行处理指纹搜索

        Args:
            fingerprints: 指纹列表
            search_func: 搜索函数
            batch_size: 批次大小
            progress_callback: 进度回调函数

        Returns:
            搜索结果列表
        """
        if not fingerprints:
            return []

        self.logger.logger.info(f"Starting parallel fingerprint search for {len(fingerprints)} fingerprints")

        def batch_search_func(fingerprint_batch: List[Dict[str, Any]]) -> List[Any]:
            """批量搜索函数"""
            return [search_func(fp) for fp in fingerprint_batch]

        def batch_progress_callback(completed: int, total: int, batch: List[Dict[str, Any]]):
            """批次处理进度回调"""
            processed_items = completed * batch_size
            total_items = len(fingerprints)
            self.logger.logger.info(f"Processed {processed_items}/{total_items} fingerprints "
                                   f"(batch {completed}/{total})")
            
            if progress_callback:
                progress_callback(processed_items, total_items, batch)

        # 使用批量处理
        results = self.processor.batch_process(
            batch_search_func,
            fingerprints,
            batch_size,
            progress_callback=batch_progress_callback
        )

        self.logger.logger.info(f"Parallel fingerprint search completed: {len(results)} results")
        return results


# 便捷函数
def parallel_map(func: Callable, items: Iterable, max_workers: int = 4,
                progress_callback: Optional[Callable] = None) -> List[Any]:
    """
    便捷的并行映射函数

    Args:
        func: 处理函数
        items: 待处理项目
        max_workers: 最大工作线程数
        progress_callback: 进度回调函数

    Returns:
        处理结果列表
    """
    processor = ParallelProcessor(max_workers)
    return processor.map(func, items, progress_callback=progress_callback)


def parallel_map_safe(func: Callable, items: Iterable, max_workers: int = 4,
                     error_handler: Optional[Callable] = None,
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    便捷的安全并行映射函数

    Args:
        func: 处理函数
        items: 待处理项目
        max_workers: 最大工作线程数
        error_handler: 错误处理函数
        progress_callback: 进度回调函数

    Returns:
        包含结果和错误信息的字典
    """
    processor = ParallelProcessor(max_workers)
    return processor.map_with_error_handling(func, items, error_handler, progress_callback)

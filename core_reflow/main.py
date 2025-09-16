#!/usr/bin/env python3
"""
MR回流验证系统 - 主入口
"""

import argparse
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config import ConfigManager
from utils.logging_config import setup_global_logging, get_structured_logger
from utils.metrics import get_metrics_collector, timer_context, count_operation
from utils.parallel import MRParallelProcessor
from utils.cache import CacheManager, MemoryCache, FileCache
from utils.exceptions import (
    CoreReflowError, ConfigurationError, GitLabAPIError, 
    GitOperationError, ValidationError
)
from utils.validators import validate_output_format, validate_days_back

from gitlab.mr_processor import MRProcessor
from git.extractor import ChangeExtractor
from fingerprint.generator import FingerprintGenerator
from git.searcher import MasterBranchSearcher
from core.validator import MatchValidator
from core.outputer import ResultOutputer


class MRReflowValidator:
    """MR回流验证器"""

    def __init__(self, config_file: str = None):
        """
        初始化验证器

        Args:
            config_file: 配置文件路径

        Raises:
            ConfigurationError: 配置错误时抛出
        """
        try:
            # 加载配置
            self.config = ConfigManager(config_file)
            
            # 设置日志
            self._setup_logging()
            
            # 设置缓存
            self._setup_cache()
            
            # 设置指标收集
            self._setup_metrics()
            
            # 初始化组件
            self._initialize_components()
            
            # 设置并行处理
            self._setup_parallel_processing()
            
            self.logger.logger.info("MRReflowValidator initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize MRReflowValidator: {e}")
            raise ConfigurationError(f"Initialization failed: {e}")

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        setup_global_logging(log_config)
        self.logger = get_structured_logger(__name__)

    def _setup_cache(self):
        """设置缓存"""
        cache_config = self.config.get('cache', {})
        backend_type = cache_config.get('backend', 'memory')
        
        if backend_type == 'memory':
            cache_backend = MemoryCache(
                max_size=cache_config.get('max_size', 1000),
                default_ttl=cache_config.get('default_ttl', 3600)
            )
        elif backend_type == 'file':
            cache_backend = FileCache(
                cache_dir=cache_config.get('cache_dir', '.cache'),
                default_ttl=cache_config.get('default_ttl', 3600)
            )
        else:
            # 默认使用内存缓存
            cache_backend = MemoryCache()
            
        self.cache_manager = CacheManager(cache_backend)

    def _setup_metrics(self):
        """设置指标收集"""
        self.metrics_collector = get_metrics_collector()
        enable_metrics = self.config.get('performance.enable_metrics', True)
        if not enable_metrics:
            # 如果禁用指标，可以设置一个空的收集器
            pass

    def _setup_parallel_processing(self):
        """设置并行处理"""
        max_workers = self.config.get('performance.max_workers', 4)
        self.parallel_processor = MRParallelProcessor(max_workers)

    def _initialize_components(self):
        """初始化各个组件"""
        try:
            # GitLab配置
            gitlab_token = self.config.get('gitlab.token')
            project_id = self.config.get('gitlab.project_id')
            gitlab_url = self.config.get('gitlab.url', 'https://gitlab.com')

            # Git配置
            repo_path = self.config.get('git.repo_path', '.')
            target_branch = self.config.get('git.target_branch', 'dev_master')
            search_days = self.config.get('git.search_days', 30)

            # 指纹配置
            ignore_patterns = self.config.get('fingerprint.ignore_patterns', [])

            # 初始化组件
            self.mr_processor = MRProcessor(gitlab_token, project_id, gitlab_url)
            self.change_extractor = ChangeExtractor(repo_path)
            self.fingerprint_gen = FingerprintGenerator(ignore_patterns)
            self.searcher = MasterBranchSearcher(
                repo_path, target_branch, 
                cache_manager=self.cache_manager,
                ignore_patterns=ignore_patterns
            )
            self.validator = MatchValidator()
            self.outputer = ResultOutputer()

            self.search_days = search_days
            
            self.logger.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.log_error("component_initialization", e)
            raise ConfigurationError(f"初始化组件失败: {e}")

    def validate_branch(self, branch_name: str) -> None:
        """
        验证指定分支的所有MR

        Args:
            branch_name: 分支名称

        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            with timer_context("validate_branch"):
                self.logger.log_operation("validate_branch", branch=branch_name)
                
                # 1. 获取MR列表
                self.logger.logger.info(f"开始验证分支: {branch_name}")
                self.logger.logger.info("1. 获取MR列表...")
                
                mrs = self.mr_processor.get_branch_mrs(branch_name)
                if not mrs:
                    self.logger.logger.warning(f"未找到分支 {branch_name} 的已合并MR")
                    return

                count_operation("mrs_found", len(mrs))
                self.logger.logger.info(f"找到 {len(mrs)} 个MR")

                # 2. 并行处理MR
                self.logger.logger.info("2. 并行处理MR变更...")
                
                def process_single_mr(mr):
                    """处理单个MR"""
                    try:
                        # 提取变更
                        changes = self.change_extractor.extract_changes(mr)
                        if not changes:
                            return []

                        # 生成指纹
                        fingerprints = self.fingerprint_gen.generate(changes, mr['id'])
                        if not fingerprints:
                            return []

                        # 在主线分支中搜索
                        search_results = self.searcher.search_changes_in_master(
                            fingerprints, self.search_days
                        )

                        # 验证结果
                        validated_results = self.validator.validate_results(search_results)
                        return validated_results

                    except Exception as e:
                        self.logger.log_error("process_single_mr", e, mr_id=mr.get('id'))
                        return []

                def progress_callback(completed, total, mr):
                    """进度回调"""
                    progress = (completed / total) * 100
                    self.logger.logger.info(f"处理进度: {completed}/{total} ({progress:.1f}%) "
                                          f"- MR #{mr.get('id', 'unknown')}")

                # 使用并行处理器
                result = self.parallel_processor.process_mrs_parallel(
                    mrs, process_single_mr, progress_callback
                )

                # 合并所有结果
                all_results = []
                for mr_results in result['results']:
                    if isinstance(mr_results, list):
                        all_results.extend(mr_results)
                    elif mr_results:
                        all_results.append(mr_results)

                # 记录统计信息
                count_operation("validation_results", len(all_results))
                matched_count = sum(1 for r in all_results if r.get('matched', False))
                count_operation("matched_results", matched_count)

                # 3. 输出结果
                self.logger.logger.info("3. 生成验证报告...")
                output_format = self.config.get('output.format', 'console')
                self.outputer.output_results(all_results, output_format)

                # 输出统计信息
                self._output_statistics(result, all_results)

        except Exception as e:
            self.logger.log_error("validate_branch", e, branch=branch_name)
            raise ValidationError(f"验证分支失败: {e}")

    def _output_statistics(self, parallel_result, all_results):
        """输出统计信息"""
        self.logger.logger.info("\n=== 验证统计信息 ===")
        self.logger.logger.info(f"并行处理统计:")
        self.logger.logger.info(f"  - 成功处理: {parallel_result['success_count']}")
        self.logger.logger.info(f"  - 处理失败: {parallel_result['error_count']}")
        
        if all_results:
            matched = sum(1 for r in all_results if r.get('matched', False))
            self.logger.logger.info(f"验证结果统计:")
            self.logger.logger.info(f"  - 总结果数: {len(all_results)}")
            self.logger.logger.info(f"  - 匹配成功: {matched}")
            self.logger.logger.info(f"  - 匹配失败: {len(all_results) - matched}")
            self.logger.logger.info(f"  - 匹配率: {matched/len(all_results)*100:.1f}%")
        
        # 输出缓存统计
        cache_stats = self.cache_manager.get_stats()
        self.logger.logger.info(f"缓存统计: 命中率 {cache_stats['hit_rate']:.2%}")
        
        # 输出性能指标
        metrics = self.metrics_collector.get_all_metrics()
        if metrics.get('timers'):
            for name, stats in metrics['timers'].items():
                if stats['count'] > 0:
                    self.logger.logger.info(f"性能指标 {name}: 平均耗时 {stats['avg_time']:.3f}s")

    def validate_mr(self, mr_id: int) -> None:
        """
        验证指定MR

        Args:
            mr_id: MR ID

        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            with timer_context("validate_mr"):
                self.logger.log_operation("validate_mr", mr_id=mr_id)
                
                # 1. 获取MR信息
                self.logger.logger.info(f"开始验证MR: #{mr_id}")
                self.logger.logger.info("1. 获取MR信息...")
                
                mr = self.mr_processor.get_mr_by_id(mr_id)
                if not mr:
                    self.logger.logger.warning(f"未找到MR #{mr_id}")
                    return

                # 2. 提取变更
                self.logger.logger.info("2. 提取变更...")
                changes = self.change_extractor.extract_changes(mr)
                count_operation("changes_extracted", len(changes) if changes else 0)

                # 3. 生成指纹
                self.logger.logger.info("3. 生成指纹...")
                fingerprints = self.fingerprint_gen.generate(changes, mr_id)
                count_operation("fingerprints_generated", len(fingerprints) if fingerprints else 0)

                if not fingerprints:
                    self.logger.logger.warning("未找到有效的代码变更")
                    return

                # 4. 在主线分支中搜索
                self.logger.logger.info("4. 搜索主线分支...")
                search_results = self.searcher.search_changes_in_master(
                    fingerprints, self.search_days
                )

                # 5. 验证结果
                self.logger.logger.info("5. 验证结果...")
                validated_results = self.validator.validate_results(search_results)
                count_operation("validation_results", len(validated_results))

                # 6. 输出结果
                self.logger.logger.info("6. 生成验证报告...")
                output_format = self.config.get('output.format', 'console')
                self.outputer.output_results(validated_results, output_format)

                # 输出单个MR的统计
                self._output_single_mr_statistics(validated_results)

        except Exception as e:
            self.logger.log_error("validate_mr", e, mr_id=mr_id)
            raise ValidationError(f"验证MR失败: {e}")

    def _output_single_mr_statistics(self, results):
        """输出单个MR的统计信息"""
        if results:
            matched = sum(1 for r in results if r.get('matched', False))
            self.logger.logger.info(f"\n=== MR验证统计 ===")
            self.logger.logger.info(f"  - 验证项目: {len(results)}")
            self.logger.logger.info(f"  - 匹配成功: {matched}")
            self.logger.logger.info(f"  - 匹配失败: {len(results) - matched}")
            
        # 输出缓存统计
        cache_stats = self.cache_manager.get_stats()
        self.logger.logger.info(f"缓存命中率: {cache_stats['hit_rate']:.2%}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MR回流验证系统 - 验证GitLab MR是否已进入主线分支',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --branch feature/auth-fix --config config.json
  %(prog)s --mr-id 123 --days 60 --output json
  %(prog)s --branch feature/new-feature --workers 8
        """
    )
    
    parser.add_argument('--branch', help='验证指定分支的所有MR')
    parser.add_argument('--mr-id', type=int, help='验证指定MR')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--days', type=int, help='搜索时间范围（天）')
    parser.add_argument('--output', choices=['console', 'json', 'markdown'],
                       help='输出格式')
    parser.add_argument('--workers', type=int, help='并行工作线程数')
    parser.add_argument('--cache-clear', action='store_true', help='清空缓存后运行')
    parser.add_argument('--metrics', action='store_true', help='显示详细的性能指标')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')

    args = parser.parse_args()

    try:
        # 初始化验证器
        validator = MRReflowValidator(args.config)

        # 验证配置
        if not validator.config.validate():
            print("❌ 配置验证失败，请检查配置文件")
            sys.exit(1)

        # 设置运行时参数
        if args.days:
            try:
                validator.search_days = validate_days_back(args.days)
            except Exception as e:
                print(f"❌ 无效的搜索天数: {e}")
                sys.exit(1)

        if args.output:
            try:
                output_format = validate_output_format(args.output)
                validator.config.set('output.format', output_format)
            except Exception as e:
                print(f"❌ 无效的输出格式: {e}")
                sys.exit(1)

        if args.workers:
            validator.parallel_processor = MRParallelProcessor(args.workers)

        # 清空缓存（如果需要）
        if args.cache_clear:
            validator.cache_manager.clear()
            print("🗑️ 缓存已清空")

        # 执行验证
        start_time = time.time()
        
        if args.branch:
            validator.validate_branch(args.branch)
        elif args.mr_id:
            validator.validate_mr(args.mr_id)
        else:
            print("❌ 请指定 --branch 或 --mr-id 参数")
            parser.print_help()
            sys.exit(1)

        # 显示总体统计
        duration = time.time() - start_time
        print(f"\n⏱️ 总耗时: {duration:.2f}秒")

        if args.metrics:
            # 显示详细指标
            metrics = validator.metrics_collector.get_all_metrics()
            print("\n📊 详细性能指标:")
            print(f"  缓存命中率: {validator.cache_manager.get_hit_rate():.2%}")
            
            if metrics.get('counters'):
                print("  操作计数:")
                for name, count in metrics['counters'].items():
                    print(f"    {name}: {count}")
                    
            if metrics.get('timers'):
                print("  性能计时:")
                for name, stats in metrics['timers'].items():
                    if stats['count'] > 0:
                        print(f"    {name}: 平均 {stats['avg_time']:.3f}s "
                              f"(最大 {stats['max_time']:.3f}s, 总计 {stats['count']} 次)")

        print("\n✅ 验证完成")

    except ConfigurationError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"❌ 验证错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 未预期的错误: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Core Reflow CLI - 命令行接口模块
提供更友好的命令行交互界面
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_reflow.main import MRReflowValidator
from core_reflow.utils.exceptions import ConfigurationError, ValidationError
from core_reflow.utils.validators import validate_output_format, validate_days_back
from core_reflow.core.delivery_validator import DeliveryBranchValidator


class CoreReflowCLI:
    """Core Reflow 命令行接口"""
    
    def __init__(self):
        self.validator = None
        self.delivery_validator = None
    
    def init_validator(self, config_file: Optional[str] = None) -> None:
        """初始化验证器"""
        try:
            self.validator = MRReflowValidator(config_file)
            print("✅ 验证器初始化成功")
        except Exception as e:
            print(f"❌ 验证器初始化失败: {e}")
            sys.exit(1)
    
    def init_delivery_validator(self, config_file: Optional[str] = None) -> None:
        """初始化交付分支验证器"""
        try:
            self.delivery_validator = DeliveryBranchValidator(config_file)
            print("✅ 交付分支验证器初始化成功")
        except Exception as e:
            print(f"❌ 交付分支验证器初始化失败: {e}")
            sys.exit(1)
    
    def validate_single_branch(self, branch_name: str, **kwargs) -> None:
        """验证单个分支"""
        if not self.validator:
            print("❌ 验证器未初始化")
            return
            
        print(f"🔍 开始验证分支: {branch_name}")
        try:
            self.validator.validate_branch(branch_name)
            print(f"✅ 分支 {branch_name} 验证完成")
        except ValidationError as e:
            print(f"❌ 验证失败: {e}")
            sys.exit(1)
    
    def validate_single_mr(self, mr_id: int, **kwargs) -> None:
        """验证单个MR"""
        if not self.validator:
            print("❌ 验证器未初始化")
            return
            
        print(f"🔍 开始验证MR: #{mr_id}")
        try:
            self.validator.validate_mr(mr_id)
            print(f"✅ MR #{mr_id} 验证完成")
        except ValidationError as e:
            print(f"❌ 验证失败: {e}")
            sys.exit(1)
    
    def validate_delivery_branch(self, delivery_branch: str, **kwargs) -> None:
        """验证交付分支"""
        if not self.delivery_validator:
            print("❌ 交付分支验证器未初始化")
            return
            
        print(f"🔍 开始验证交付分支: {delivery_branch}")
        try:
            self.delivery_validator.validate_delivery_branch(delivery_branch)
            print(f"✅ 交付分支 {delivery_branch} 验证完成")
        except ValidationError as e:
            print(f"❌ 验证失败: {e}")
            sys.exit(1)
    
    def validate_multi_repo(self, config_file: str, **kwargs) -> None:
        """验证多仓库配置"""
        if not os.path.exists(config_file):
            print(f"❌ 配置文件不存在: {config_file}")
            sys.exit(1)
            
        print(f"🔍 开始验证多仓库配置: {config_file}")
        try:
            # 读取多仓库配置
            with open(config_file, 'r', encoding='utf-8') as f:
                multi_config = json.load(f)
            
            repositories = multi_config.get('repositories', [])
            if not repositories:
                print("❌ 配置文件中未找到仓库列表")
                sys.exit(1)
            
            for i, repo_config in enumerate(repositories, 1):
                repo_name = repo_config.get('name', f'Repository-{i}')
                print(f"\n📂 [{i}/{len(repositories)}] 验证仓库: {repo_name}")
                
                # 为每个仓库创建验证器
                delivery_validator = DeliveryBranchValidator()
                delivery_validator.load_config_from_dict(repo_config)
                
                # 执行验证
                delivery_branches = repo_config.get('delivery_branches', [])
                for branch in delivery_branches:
                    delivery_validator.validate_delivery_branch(branch)
            
            print(f"\n✅ 所有 {len(repositories)} 个仓库验证完成")
            
        except Exception as e:
            print(f"❌ 多仓库验证失败: {e}")
            sys.exit(1)
    
    def show_config_example(self, config_type: str = 'single') -> None:
        """显示配置文件示例"""
        if config_type == 'single':
            print("📋 单仓库配置示例 (config.json):")
            print("""
{
  "gitlab": {
    "url": "https://gitlab.example.com",
    "token": "your-gitlab-token",
    "project_id": "123"
  },
  "git": {
    "repo_path": "/path/to/your/repo",
    "target_branch": "dev_master",
    "search_days": 30
  },
  "fingerprint": {
    "ignore_patterns": [
      "*.md",
      "*.txt",
      "tests/*"
    ]
  },
  "output": {
    "format": "console"
  },
  "performance": {
    "max_workers": 4,
    "enable_metrics": true
  },
  "cache": {
    "backend": "memory",
    "max_size": 1000,
    "default_ttl": 3600
  },
  "logging": {
    "level": "INFO",
    "format": "structured",
    "file": "logs/core_reflow.log"
  }
}
            """)
        elif config_type == 'delivery':
            print("📋 多仓库配置示例 (delivery_config.json):")
            print("""
{
  "repositories": [
    {
      "name": "Backend API",
      "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "your-gitlab-token",
        "project_id": "123"
      },
      "git": {
        "repo_path": "/path/to/backend",
        "target_branch": "dev_master"
      },
      "delivery_branches": [
        "delivery/v1.0.0",
        "delivery/v1.1.0"
      ]
    },
    {
      "name": "Frontend App",
      "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "your-gitlab-token",
        "project_id": "456"
      },
      "git": {
        "repo_path": "/path/to/frontend",
        "target_branch": "main"
      },
      "delivery_branches": [
        "delivery/v2.0.0"
      ]
    }
  ],
  "global_settings": {
    "search_days": 30,
    "max_workers": 8,
    "output_format": "json"
  }
}
            """)
    
    def interactive_setup(self) -> None:
        """交互式配置设置"""
        print("🚀 Core Reflow 交互式配置向导")
        print("=" * 50)
        
        config = {}
        
        # GitLab 配置
        print("\n📡 GitLab 配置:")
        config['gitlab'] = {
            'url': input("GitLab URL (默认: https://gitlab.com): ") or "https://gitlab.com",
            'token': input("GitLab Token: ").strip(),
            'project_id': input("Project ID: ").strip()
        }
        
        if not config['gitlab']['token'] or not config['gitlab']['project_id']:
            print("❌ GitLab token 和 project_id 是必需的")
            sys.exit(1)
        
        # Git 配置
        print("\n📁 Git 配置:")
        config['git'] = {
            'repo_path': input("仓库路径 (默认: 当前目录): ") or ".",
            'target_branch': input("目标分支 (默认: dev_master): ") or "dev_master",
            'search_days': int(input("搜索天数 (默认: 30): ") or "30")
        }
        
        # 输出配置
        print("\n📤 输出配置:")
        output_format = input("输出格式 [console/json/markdown] (默认: console): ") or "console"
        config['output'] = {'format': output_format}
        
        # 性能配置
        print("\n⚡ 性能配置:")
        config['performance'] = {
            'max_workers': int(input("最大并行数 (默认: 4): ") or "4"),
            'enable_metrics': input("启用性能指标? [y/N]: ").lower().startswith('y')
        }
        
        # 保存配置
        config_file = input("\n💾 配置文件名 (默认: config.json): ") or "config.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 配置已保存到: {config_file}")
            print("\n🎉 配置完成！现在可以使用以下命令:")
            print(f"  core-reflow-cli --branch your-branch --config {config_file}")
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            sys.exit(1)


def main():
    """CLI主函数"""
    parser = argparse.ArgumentParser(
        description='Core Reflow CLI - MR回流验证系统命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --branch feature/auth-fix
  %(prog)s --mr-id 123 --output json
  %(prog)s --delivery-branch delivery/v1.0.0
  %(prog)s --multi-repo delivery_config.json
  %(prog)s --interactive
  %(prog)s --config-example single
        """
    )
    
    # 验证操作参数
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--branch', help='验证指定分支的所有MR')
    group.add_argument('--mr-id', type=int, help='验证指定MR')
    group.add_argument('--delivery-branch', help='验证交付分支')
    group.add_argument('--multi-repo', help='验证多仓库配置文件')
    group.add_argument('--interactive', action='store_true', help='交互式配置向导')
    group.add_argument('--config-example', choices=['single', 'delivery'], 
                       help='显示配置文件示例')
    
    # 配置参数
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--days', type=int, help='搜索时间范围（天）')
    parser.add_argument('--output', choices=['console', 'json', 'markdown'],
                       help='输出格式')
    parser.add_argument('--workers', type=int, help='并行工作线程数')
    parser.add_argument('--cache-clear', action='store_true', help='清空缓存后运行')
    parser.add_argument('--metrics', action='store_true', help='显示详细的性能指标')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    
    # 如果没有提供任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    cli = CoreReflowCLI()
    
    try:
        # 特殊命令处理
        if args.interactive:
            cli.interactive_setup()
            return
        
        if args.config_example:
            cli.show_config_example(args.config_example)
            return
        
        # 确保有操作参数
        if not any([args.branch, args.mr_id, args.delivery_branch, args.multi_repo]):
            print("❌ 请指定一个验证操作参数")
            parser.print_help()
            sys.exit(1)
        
        # 初始化验证器
        if args.delivery_branch:
            cli.init_delivery_validator(args.config)
        elif args.multi_repo:
            pass  # 多仓库验证会自己处理初始化
        else:
            cli.init_validator(args.config)
            
            # 应用运行时参数
            if args.days:
                cli.validator.search_days = validate_days_back(args.days)
            
            if args.output:
                output_format = validate_output_format(args.output)
                cli.validator.config.set('output.format', output_format)
            
            if args.workers:
                from core_reflow.utils.parallel import MRParallelProcessor
                cli.validator.parallel_processor = MRParallelProcessor(args.workers)
            
            if args.cache_clear:
                cli.validator.cache_manager.clear()
                print("🗑️ 缓存已清空")
        
        # 执行验证操作
        if args.branch:
            cli.validate_single_branch(args.branch)
        elif args.mr_id:
            cli.validate_single_mr(args.mr_id)
        elif args.delivery_branch:
            cli.validate_delivery_branch(args.delivery_branch)
        elif args.multi_repo:
            cli.validate_multi_repo(args.multi_repo)
        
        print("\n🎉 所有操作完成！")
        
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

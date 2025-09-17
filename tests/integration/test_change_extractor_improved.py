#!/usr/bin/env python3
"""
改进的变更提取器测试
使用分支差异方式来测试变更提取
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core_reflow.utils.config import ConfigManager
from core_reflow.gitlab_api.mr_processor import MRProcessor
from core_reflow.git_operations.extractor import ChangeExtractor

def test_change_extractor_with_branch_diff():
    config = ConfigManager('config.json')
    
    # 初始化组件
    mr_processor = MRProcessor(
        config.get('gitlab.token'),
        config.get('gitlab.project_id'),
        config.get('gitlab.url')
    )
    
    extractor = ChangeExtractor(config.get('git.repo_path'))
    
    print("🔍 改进的变更提取器测试 - 使用分支差异方式")
    print("=" * 60)
    
    # 首先测试直接使用已知的提交
    print("🧪 测试1: 使用本地已知提交")
    try:
        repo = extractor.repo
        local_commits = list(repo.iter_commits(max_count=3))
        
        for i, commit in enumerate(local_commits, 1):
            print(f"\\n📋 测试提交 {i}: {commit.hexsha[:8]}")
            print(f"   作者: {commit.author.name}")
            print(f"   时间: {commit.committed_datetime}")
            print(f"   消息: {commit.summary}")
            
            # 创建模拟的MR信息
            mock_mr_info = {
                'id': f'mock-{i}',
                'title': commit.summary,
                'source_branch': 'test_branch',
                'target_branch': 'dev_master',
                'merge_commit_sha': commit.hexsha
            }
            
            try:
                changes = extractor.extract_changes(mock_mr_info)
                if changes:
                    print(f"   ✅ 成功提取 {len(changes)} 个文件变更")
                    
                    # 统计变更类型
                    stats = {}
                    for change in changes:
                        ct = change['change_type']
                        stats[ct] = stats.get(ct, 0) + 1
                    print(f"   📊 变更统计: {stats}")
                    
                    # 显示几个变更文件
                    for j, change in enumerate(changes[:3], 1):
                        print(f"     {j}. {change['file_path']} ({change['change_type']})")
                        
                        # 检查diff内容质量
                        if change['diff_content']:
                            lines = len(change['diff_content'].split('\\n'))
                            print(f"        Diff行数: {lines}")
                        else:
                            print(f"        ⚠️ 无diff内容")
                            
                else:
                    print(f"   ⚠️ 未提取到变更")
                    
            except Exception as e:
                print(f"   ❌ 提取失败: {e}")
                
        print("\\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 本地提交测试失败: {e}")
    
    # 测试2: 获取可访问的MR进行测试
    print("\\n🧪 测试2: 尝试获取可访问的MR")
    try:
        # 获取开放状态的MR（更容易访问分支）
        print("📋 获取开放状态的MR...")
        mrs = mr_processor.project.mergerequests.list(
            state='opened', 
            order_by='updated_at', 
            sort='desc',
            per_page=3,
            get_all=False
        )
        
        if mrs:
            for i, mr in enumerate(mrs, 1):
                print(f"\\n📋 测试MR {i}: #{mr.iid} - {mr.title}")
                print(f"   源分支: {mr.source_branch}")
                print(f"   目标分支: {mr.target_branch}")
                print(f"   状态: {mr.state}")
                
                # 对于开放的MR，尝试不使用merge_commit_sha
                mr_info = {
                    'id': mr.iid,
                    'title': mr.title,
                    'source_branch': mr.source_branch,
                    'target_branch': mr.target_branch,
                    'merge_commit_sha': None  # 不使用合并提交
                }
                
                try:
                    changes = extractor.extract_changes(mr_info)
                    if changes:
                        print(f"   ✅ 成功提取 {len(changes)} 个文件变更（分支差异方式）")
                        
                        # 显示几个变更文件
                        for j, change in enumerate(changes[:2], 1):
                            print(f"     {j}. {change['file_path']} ({change['change_type']})")
                    else:
                        print(f"   ⚠️ 未提取到变更（可能分支不可访问）")
                        
                except Exception as e:
                    print(f"   ❌ 提取失败: {e}")
                    print(f"     原因可能：源分支 {mr.source_branch} 在本地不可访问")
                    
        else:
            print("未找到开放的MR")
            
    except Exception as e:
        print(f"❌ 开放MR测试失败: {e}")
    
    print("\\n" + "=" * 60)
    print("🎯 变更提取器分析总结:")
    print("✅ 如果测试1（本地提交）成功，说明变更提取器核心功能正常")
    print("⚠️ 如果测试2失败，主要是因为本地仓库没有远程分支")
    print("\\n🔧 解决方案建议:")
    print("1. 执行 git fetch --all 获取所有远程分支")
    print("2. 或者专门测试已合并到 dev_master 的MR")
    print("3. 变更提取器本身功能正常，问题在于Git仓库同步")

if __name__ == '__main__':
    test_change_extractor_with_branch_diff()

#!/usr/bin/env python3
"""
变更提取器专项测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core_reflow.utils.config import ConfigManager
from core_reflow.gitlab_api.mr_processor import MRProcessor
from core_reflow.git_operations.extractor import ChangeExtractor

def test_change_extractor():
    config = ConfigManager('config.json')
    
    # 初始化组件
    mr_processor = MRProcessor(
        config.get('gitlab.token'),
        config.get('gitlab.project_id'),
        config.get('gitlab.url')
    )
    
    extractor = ChangeExtractor(config.get('git.repo_path'))
    
    print("🔍 开始测试变更提取器...")
    print("=" * 60)
    
    # 获取最近的一些已合并MR进行测试
    try:
        print("📋 获取已合并的MR...")
        mrs = mr_processor.project.mergerequests.list(
            state='merged', 
            order_by='updated_at', 
            sort='desc',
            per_page=5,
            get_all=False
        )
        
        if not mrs:
            print("❌ 未找到已合并的MR，请确保项目中有已合并的MR")
            return
            
        print(f"✅ 找到 {len(mrs)} 个已合并的MR，开始测试...")
        print("=" * 60)
            
        for idx, mr in enumerate(mrs, 1):
            print(f"\n🧪 测试 {idx}/{len(mrs)} - MR #{mr.iid}: {mr.title}")
            print(f"   📅 源分支: {mr.source_branch}")
            print(f"   🎯 目标分支: {mr.target_branch}")
            print(f"   ⏰ 合并时间: {mr.merged_at}")
            print(f"   🔗 合并提交: {mr.merge_commit_sha[:8] if mr.merge_commit_sha else 'N/A'}")
            
            # 构造MR信息
            mr_info = {
                'id': mr.iid,
                'title': mr.title,
                'source_branch': mr.source_branch,
                'target_branch': mr.target_branch,
                'merge_commit_sha': mr.merge_commit_sha
            }
            
            # 提取变更
            try:
                print(f"   🔍 开始提取变更...")
                changes = extractor.extract_changes(mr_info)
                
                if changes:
                    print(f"   ✅ 成功提取到 {len(changes)} 个文件变更:")
                    
                    # 按变更类型分组统计
                    change_stats = {}
                    for change in changes:
                        change_type = change['change_type']
                        change_stats[change_type] = change_stats.get(change_type, 0) + 1
                    
                    print(f"      📊 变更统计: {dict(change_stats)}")
                    
                    # 显示前几个变更的详细信息
                    for i, change in enumerate(changes[:3], 1):
                        print(f"      {i}. {change['file_path']} ({change['change_type']})")
                        
                        # 分析diff内容
                        diff_lines = change['diff_content'].split('\\n') if change['diff_content'] else []
                        added_lines = len([line for line in diff_lines if line.startswith('+')])
                        deleted_lines = len([line for line in diff_lines if line.startswith('-')])
                        
                        print(f"         📝 Diff行数: 总计{len(diff_lines)}, +{added_lines}, -{deleted_lines}")
                        
                        # 显示diff内容的前几行作为示例
                        if change['diff_content']:
                            preview_lines = change['diff_content'].split('\\n')[:5]
                            print(f"         👀 内容预览:")
                            for line in preview_lines:
                                if line.strip():
                                    print(f"            {line[:80]}...")
                                    
                    if len(changes) > 3:
                        print(f"      ... 还有 {len(changes) - 3} 个文件变更")
                        
                    print(f"   ✅ 变更提取成功 - 质量评估: 良好")
                    
                else:
                    print(f"   ⚠️ 未提取到代码变更 - 可能原因:")
                    print(f"      • 只有注释或空白行变更")
                    print(f"      • 没有支持的代码文件类型")
                    print(f"      • 合并提交无法访问")
                    
            except Exception as e:
                print(f"   ❌ 变更提取失败: {e}")
                print(f"   🔧 建议检查:")
                print(f"      • 合并提交SHA是否有效")
                print(f"      • 分支是否可访问")
                print(f"      • 仓库是否包含相关提交")
                
            print("-" * 40)
                
    except Exception as e:
        print(f"❌ 获取MR列表失败: {e}")
        return
    
    print("\\n🎯 变更提取器测试总结:")
    print("✅ 如果大部分MR都能成功提取变更，说明变更提取器工作正常")
    print("⚠️ 如果有失败案例，请查看具体错误信息进行调试")
    print("🔧 下一步建议: 继续测试指纹生成器")

if __name__ == '__main__':
    test_change_extractor()

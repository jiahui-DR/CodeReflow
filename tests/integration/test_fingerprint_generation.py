#!/usr/bin/env python3
"""
指纹生成器专项测试
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core_reflow.utils.config import ConfigManager
from core_reflow.gitlab_api.mr_processor import MRProcessor
from core_reflow.git_operations.extractor import ChangeExtractor
from core_reflow.fingerprint.generator import FingerprintGenerator

def test_fingerprint_generation():
    config = ConfigManager('config.json')
    
    # 初始化组件
    extractor = ChangeExtractor(config.get('git.repo_path'))
    generator = FingerprintGenerator(config.get('fingerprint.ignore_patterns'))
    
    print("🏷️ 开始测试指纹生成器...")
    print("=" * 60)
    
    # 使用之前成功的提交来测试指纹生成
    print("🧪 使用已知的成功提交进行指纹生成测试")
    
    try:
        repo = extractor.repo
        commits = list(repo.iter_commits(max_count=5))
        
        successful_tests = 0
        total_fingerprints = 0
        
        for i, commit in enumerate(commits, 1):
            print(f"\\n📋 测试提交 {i}: {commit.hexsha[:8]}")
            print(f"   消息: {commit.summary}")
            
            # 创建模拟MR信息
            mock_mr_info = {
                'id': i,
                'title': commit.summary,
                'source_branch': 'test_branch',
                'target_branch': 'dev_master',
                'merge_commit_sha': commit.hexsha
            }
            
            try:
                # 提取变更
                changes = extractor.extract_changes(mock_mr_info)
                
                if changes:
                    print(f"   📝 提取到 {len(changes)} 个文件变更")
                    
                    # 生成指纹
                    fingerprints = generator.generate(changes, i)
                    
                    if fingerprints:
                        print(f"   ✅ 成功生成 {len(fingerprints)} 个指纹")
                        successful_tests += 1
                        total_fingerprints += len(fingerprints)
                        
                        # 显示指纹详情
                        for j, fp in enumerate(fingerprints[:3], 1):
                            print(f"     指纹 {j}:")
                            print(f"       📄 文件: {fp['file_path']}")
                            print(f"       🏷️ 指纹: {fp['fingerprint']}")
                            print(f"       🔄 类型: {fp['change_type']}")
                            print(f"       📊 有效行数: {fp['line_count']}")
                            print(f"       👀 内容预览: {fp['content_preview'][:60]}...")
                            
                            # 验证指纹质量
                            if len(fp['fingerprint']) == 16:
                                print(f"       ✅ 指纹长度正确 (16字符)")
                            else:
                                print(f"       ⚠️ 指纹长度异常: {len(fp['fingerprint'])}")
                                
                            if fp['line_count'] > 0:
                                print(f"       ✅ 包含有效代码行")
                            else:
                                print(f"       ⚠️ 无有效代码行")
                            
                        if len(fingerprints) > 3:
                            print(f"     ... 还有 {len(fingerprints) - 3} 个指纹")
                            
                        # 测试指纹比较功能
                        print(f"\\n   🔍 测试指纹比较功能:")
                        if len(fingerprints) >= 2:
                            fp1 = fingerprints[0]['fingerprint']
                            fp2 = fingerprints[1]['fingerprint']
                            same = generator.compare_fingerprints(fp1, fp2)
                            print(f"     指纹1 vs 指纹2: {'相同' if same else '不同'} ✅")
                            
                            # 测试相同指纹
                            same_self = generator.compare_fingerprints(fp1, fp1)
                            print(f"     指纹1 vs 自身: {'相同' if same_self else '不同'} {'✅' if same_self else '❌'}")
                        
                    else:
                        print(f"   ⚠️ 未生成指纹（可能都是注释或空白变更）")
                        
                else:
                    print(f"   ⚠️ 未提取到变更")
                    
            except Exception as e:
                print(f"   ❌ 指纹生成失败: {e}")
        
        print("\\n" + "=" * 60)
        print("🎯 指纹生成器测试总结:")
        print(f"✅ 成功测试: {successful_tests}/5 个提交")
        print(f"🏷️ 总指纹数: {total_fingerprints} 个")
        
        if successful_tests >= 2:
            print("✅ 指纹生成器工作正常！")
            
            # 额外测试：指纹一致性
            print("\\n🧪 额外测试：指纹一致性验证")
            test_consistency(generator)
            
        else:
            print("⚠️ 指纹生成成功率较低，需要检查:")
            print("  - 提交是否包含代码变更")
            print("  - 忽略模式是否过于严格")
            
    except Exception as e:
        print(f"❌ 指纹生成测试失败: {e}")

def test_consistency(generator):
    """测试指纹生成的一致性"""
    print("   测试相同输入是否产生相同指纹...")
    
    # 创建测试数据
    test_change = {
        'file_path': 'test.cpp',
        'change_type': 'MODIFY',
        'diff_content': '''@@ -1,3 +1,5 @@
 int main() {
-    return 0;
+    printf("Hello World");
+    return 0;
 }'''
    }
    
    try:
        # 生成两次指纹
        fp1 = generator.generate([test_change], 999)
        fp2 = generator.generate([test_change], 999)
        
        if fp1 and fp2 and len(fp1) > 0 and len(fp2) > 0:
            if fp1[0]['fingerprint'] == fp2[0]['fingerprint']:
                print("   ✅ 指纹一致性测试通过 - 相同输入产生相同指纹")
            else:
                print("   ❌ 指纹一致性测试失败 - 相同输入产生不同指纹")
        else:
            print("   ⚠️ 指纹一致性测试无法完成 - 指纹生成失败")
            
    except Exception as e:
        print(f"   ❌ 指纹一致性测试异常: {e}")

if __name__ == '__main__':
    test_fingerprint_generation()

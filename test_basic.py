#!/usr/bin/env python3
"""
基础功能测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / 'core_reflow'
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    try:
        from utils.config import ConfigManager
        from gitlab.mr_processor import MRProcessor
        from git.extractor import ChangeExtractor
        from fingerprint.generator import FingerprintGenerator
        from git.searcher import MasterBranchSearcher
        from core.validator import MatchValidator
        from core.outputer import ResultOutputer
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置管理"""
    try:
        from utils.config import ConfigManager

        # 创建默认配置
        config = ConfigManager()
        config.set('test.value', 'hello world')

        value = config.get('test.value')
        if value == 'hello world':
            print("✅ 配置管理功能正常")
            return True
        else:
            print("❌ 配置管理功能异常")
            return False
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_fingerprint():
    """测试指纹生成"""
    try:
        from fingerprint.generator import FingerprintGenerator

        generator = FingerprintGenerator()

        # 测试数据
        test_changes = [{
            'file_path': 'test.py',
            'change_type': 'MODIFY',
            'diff_content': '''@@ -1,3 +1,5 @@
 def hello():
-    print("world")
+    print("hello world")
+    return True
'''
        }]

        fingerprints = generator.generate(test_changes)
        if fingerprints and len(fingerprints[0]['fingerprint']) == 16:
            print("✅ 指纹生成功能正常")
            return True
        else:
            print("❌ 指纹生成功能异常")
            return False
    except Exception as e:
        print(f"❌ 指纹测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始运行基础功能测试...\n")

    tests = [
        ("模块导入", test_imports),
        ("配置管理", test_config),
        ("指纹生成", test_fingerprint),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"运行测试: {test_name}")
        if test_func():
            passed += 1
        print()

    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())

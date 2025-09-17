#!/usr/bin/env python3
"""
测试运行脚本
运行所有单元测试和集成测试
"""

import sys
import unittest
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有测试"""
    # 设置测试目录
    test_dir = project_root / 'tests'
    
    # 发现并运行测试
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()

def run_specific_test(test_name):
    """运行特定测试"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """主函数"""
    print("🧪 运行MR回流验证系统测试")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        print(f"运行测试: {test_name}")
        success = run_specific_test(test_name)
    else:
        # 运行所有测试
        print("运行所有测试...")
        success = run_all_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())

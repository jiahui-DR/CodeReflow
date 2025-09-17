#!/usr/bin/env python3
"""
MR回流验证系统使用示例
演示如何使用各个组件来验证MR是否已进入主线分支
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def demo_basic_usage():
    """基础使用示例"""
    print("=== MR回流验证系统使用示例 ===\n")

    # 1. 导入组件
    print("1. 导入组件...")
    from core_reflow.utils.config import ConfigManager
    from core_reflow.fingerprint.generator import FingerprintGenerator
    print("✅ 组件导入成功\n")

    # 2. 创建配置管理器（演示模式，不验证配置）
    print("2. 创建配置管理器...")
    try:
        config = ConfigManager()
        # 为演示设置一些基础配置，避免验证失败
        config.set('gitlab.token', 'demo-token')
        config.set('gitlab.project_id', 12345)
        config.set('git.repo_path', '.')
        config.set('git.target_branch', 'dev_master')
        print("✅ 配置管理器创建成功\n")
    except Exception as e:
        print(f"⚠️ 配置管理器创建失败: {e}")
        print("✅ 继续演示其他功能\n")
        config = None

    # 3. 创建指纹生成器
    print("3. 创建指纹生成器...")
    generator = FingerprintGenerator()
    print("✅ 指纹生成器创建成功\n")

    # 4. 模拟MR变更数据
    print("4. 模拟MR变更数据...")
    sample_changes = [
        {
            'file_path': 'src/user_service.py',
            'change_type': 'MODIFY',
            'diff_content': '''@@ -15,7 +15,8 @@ class UserService:
     def authenticate(self, username, password):
         # 验证用户凭据
         user = self.user_repo.find_by_username(username)
-        if not user:
+        if not user or not user.is_active:
             return None

         # 验证密码
@@ -25,6 +26,8 @@ class UserService:
         if not self.password_hasher.verify(password, user.password_hash):
             return None

+        # 记录登录时间
+        self.audit_logger.log_login(user.id)
         return user
'''
        },
        {
            'file_path': 'tests/test_user_service.py',
            'change_type': 'ADD',
            'diff_content': '''@@ -0,0 +1,15 @@ import pytest
+from src.user_service import UserService
+
+class TestUserService:
+    def test_authenticate_inactive_user(self):
+        service = UserService()
+        result = service.authenticate("inactive_user", "password")
+        assert result is None
+
+    def test_authenticate_valid_user(self):
+        service = UserService()
+        user = service.authenticate("valid_user", "password")
+        assert user is not None
+        assert user.is_active == True
'''
        }
    ]
    print("✅ 模拟数据创建成功\n")

    # 5. 生成指纹
    print("5. 生成指纹...")
    fingerprints = generator.generate(sample_changes, mr_id=123)
    print(f"✅ 生成 {len(fingerprints)} 个指纹")

    for i, fp in enumerate(fingerprints, 1):
        print(f"   指纹{i}: {fp['fingerprint']} ({fp['file_path']})")
    print()

    # 6. 演示指纹比较
    print("6. 演示指纹比较...")

    # 创建相同的变更
    same_changes = sample_changes.copy()
    same_fingerprints = generator.generate(same_changes, mr_id=123)

    # 比较指纹
    match_count = 0
    for orig_fp in fingerprints:
        for same_fp in same_fingerprints:
            if orig_fp['fingerprint'] == same_fp['fingerprint']:
                match_count += 1
                break

    print(f"✅ 相同变更的匹配率: {match_count}/{len(fingerprints)}")
    print()

    return True

def demo_workflow():
    """完整工作流程示例"""
    print("=== 完整工作流程示例 ===\n")

    # 模拟一个完整的验证流程
    print("模拟验证流程:")
    print("1. 🔍 获取MR信息")
    print("2. 📝 提取代码变更")
    print("3. 🏷️ 生成变更指纹")
    print("4. 🔎 在主线分支中搜索")
    print("5. ✅ 验证匹配结果")
    print("6. 📊 输出验证报告")
    print()

    # 模拟验证结果
    mock_results = [
        {
            'mr_id': 123,
            'file_path': 'src/user_service.py',
            'matched': True,
            'match_commit': 'a1b2c3d4',
            'match_type': 'direct_match',
            'confidence': 1.0,
            'conclusion': '已进入主线',
            'reason': '通过直接匹配确认已进入主线分支，匹配提交: a1b2c3d4',
            'recommendation': '无需操作'
        },
        {
            'mr_id': 124,
            'file_path': 'src/payment_service.py',
            'matched': False,
            'match_commit': '',
            'match_type': 'none',
            'confidence': 0.0,
            'conclusion': '未进入主线',
            'reason': '在主线分支中未找到匹配的变更',
            'recommendation': '需要推动合并到主线'
        }
    ]

    # 输出结果
    from core_reflow.core.outputer import ResultOutputer
    outputer = ResultOutputer()
    print("验证结果:")
    outputer.output_results(mock_results, 'console')

    return True

def show_command_usage():
    """显示命令行使用方法"""
    print("=== 命令行使用方法 ===\n")

    print("1. 验证指定分支的所有MR:")
    print("   python core_reflow/main.py --branch feature/auth-fix")
    print()

    print("2. 验证特定MR:")
    print("   python core_reflow/main.py --mr-id 123")
    print()

    print("3. 指定配置文件:")
    print("   python core_reflow/main.py --branch feature/auth-fix --config my_config.json")
    print()

    print("4. 自定义搜索时间范围:")
    print("   python core_reflow/main.py --branch feature/auth-fix --days 60")
    print()

    print("5. 输出为JSON格式:")
    print("   python core_reflow/main.py --branch feature/auth-fix --output json")
    print()

    print("6. 显示帮助:")
    print("   python core_reflow/main.py --help")
    print()

def show_config_example():
    """显示配置示例"""
    print("=== 配置文件示例 ===\n")

    config_content = '''{
  "gitlab": {
    "url": "https://gitlab.yourcompany.com",
    "token": "your-gitlab-personal-access-token",
    "project_id": 12345
  },
  "git": {
    "repo_path": "/path/to/your/git/repository",
    "target_branch": "dev_master",
    "search_days": 30
  },
  "fingerprint": {
    "ignore_patterns": [
      "^\\s*#.*$",
      "^\\s*$",
      "^\\s*import",
      "^\\s*from.*import"
    ]
  },
  "output": {
    "format": "console",
    "verbose": false
  }
}'''

    print("config.json:")
    print(config_content)
    print()

def main():
    """主函数"""
    try:
        # 运行演示
        print("🚀 MR回流验证系统演示")
        print("=" * 50)
        print()

        # 基础使用示例
        demo_basic_usage()

        # 完整工作流程
        demo_workflow()

        # 命令行使用方法
        show_command_usage()

        # 配置示例
        show_config_example()

        print("🎉 演示完成！")
        print("\n💡 提示:")
        print("   - 配置你的GitLab token和项目信息")
        print("   - 设置正确的仓库路径")
        print("   - 运行测试验证配置是否正确")
        print("   - 开始使用系统验证MR回流状态")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())

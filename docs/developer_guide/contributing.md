# 贡献指南

欢迎为 Core Reflow 项目做出贡献！本指南将帮助您了解如何参与项目开发、提交代码和改进系统。

## 🎯 贡献方式

### 1. 代码贡献
- 修复 Bug
- 添加新功能
- 性能优化
- 代码重构

### 2. 文档贡献
- 改进用户文档
- 添加 API 文档
- 编写教程和示例
- 翻译文档

### 3. 测试贡献
- 编写单元测试
- 添加集成测试
- 性能测试
- 兼容性测试

### 4. 其他贡献
- 报告 Bug
- 提出功能请求
- 改进设计
- 社区支持

## 🚀 快速开始

### 1. 准备开发环境

```bash
# 1. Fork 项目到您的账户
# 2. 克隆您的 fork
git clone https://github.com/your-username/core-reflow.git
cd core-reflow

# 3. 设置上游仓库
git remote add upstream https://github.com/original/core-reflow.git

# 4. 设置开发环境
./scripts/setup_dev.sh
```

### 2. 创建功能分支

```bash
# 从最新的主分支创建功能分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# 或者修复 Bug
git checkout -b bugfix/issue-number-description
```

### 3. 开发和测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 进行开发...

# 运行测试
python -m pytest tests/

# 代码格式化
./scripts/format_code.sh

# 运行完整检查
./scripts/format_code.sh --all
```

### 4. 提交代码

```bash
# 添加变更
git add .

# 提交（使用规范的提交信息）
git commit -m "feat: add new validation feature"

# 推送到您的 fork
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 访问 GitHub 仓库页面
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写 PR 描述
5. 提交 PR

## 📝 代码规范

### 1. 代码风格

我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **flake8**: 代码风格检查
- **isort**: 导入语句排序
- **mypy**: 类型检查

```bash
# 自动格式化代码
black core_reflow/ tests/

# 检查代码风格
flake8 core_reflow/ tests/

# 排序导入
isort core_reflow/ tests/

# 类型检查
mypy core_reflow/
```

### 2. 命名规范

#### 文件和目录
```python
# 使用小写字母和下划线
user_validator.py
mr_processor.py
git_operations/
```

#### 类名
```python
# 使用大驼峰命名法
class MRProcessor:
    pass

class DeliveryBranchValidator:
    pass
```

#### 函数和变量
```python
# 使用小写字母和下划线
def validate_branch(branch_name: str) -> List[Dict]:
    mr_count = 0
    validation_results = []
```

#### 常量
```python
# 使用大写字母和下划线
DEFAULT_TIMEOUT = 30
MAX_WORKERS = 8
API_BASE_URL = "https://gitlab.com/api/v4"
```

### 3. 文档字符串

使用 Google 风格的文档字符串：

```python
def validate_mr(self, mr_id: int) -> List[Dict[str, Any]]:
    """
    验证指定MR是否已进入主线分支
    
    Args:
        mr_id: MR ID，必须为正整数
        
    Returns:
        验证结果列表，每个元素包含：
        - mr_id (int): MR ID
        - matched (bool): 是否匹配
        - confidence (float): 匹配置信度 (0-1)
        - details (dict): 匹配详情
        
    Raises:
        ValidationError: 当验证过程失败时抛出
        GitLabAPIError: 当GitLab API调用失败时抛出
        
    Example:
        >>> validator = MRReflowValidator()
        >>> results = validator.validate_mr(123)
        >>> print(f"匹配状态: {results[0]['matched']}")
    """
```

### 4. 类型注解

使用 Python 类型注解提高代码可读性：

```python
from typing import List, Dict, Optional, Union, Any

class MRProcessor:
    def __init__(self, token: str, project_id: Union[str, int]) -> None:
        self.token = token
        self.project_id = str(project_id)
    
    def get_mrs(self, branch: str) -> List[Dict[str, Any]]:
        """获取MR列表"""
        pass
    
    def find_mr(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """查找特定MR"""
        pass
```

## 🧪 测试规范

### 1. 测试结构

```
tests/
├── unit/                  # 单元测试
│   ├── test_config.py
│   ├── test_cache.py
│   └── test_validators.py
├── integration/           # 集成测试
│   ├── test_gitlab_api.py
│   └── test_full_workflow.py
├── fixtures/              # 测试数据
│   ├── sample_config.json
│   └── sample_mrs.json
└── conftest.py           # pytest 配置
```

### 2. 测试命名

```python
class TestMRProcessor:
    """MR处理器测试类"""
    
    def test_get_branch_mrs_success(self):
        """测试成功获取分支MR"""
        pass
    
    def test_get_branch_mrs_empty_branch(self):
        """测试空分支情况"""
        pass
    
    def test_get_branch_mrs_api_error(self):
        """测试API错误情况"""
        pass
```

### 3. 测试覆盖率

- 目标代码覆盖率：**80%** 以上
- 关键模块覆盖率：**90%** 以上

```bash
# 运行覆盖率测试
python -m pytest tests/ --cov=core_reflow --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 4. 测试示例

```python
import pytest
from unittest.mock import Mock, patch
from core_reflow.gitlab_api.mr_processor import MRProcessor

class TestMRProcessor:
    """MR处理器测试"""
    
    @pytest.fixture
    def mr_processor(self):
        """创建MR处理器实例"""
        return MRProcessor("test-token", "123", "https://gitlab.test.com")
    
    @patch('core_reflow.gitlab_api.mr_processor.gitlab.Gitlab')
    def test_get_branch_mrs_success(self, mock_gitlab, mr_processor):
        """测试成功获取分支MR"""
        # 准备测试数据
        mock_mr = Mock()
        mock_mr.attributes = {
            'id': 123,
            'title': 'Test MR',
            'state': 'merged'
        }
        mock_gitlab.return_value.projects.get.return_value.mergerequests.list.return_value = [mock_mr]
        
        # 执行测试
        results = mr_processor.get_branch_mrs('feature/test')
        
        # 验证结果
        assert len(results) == 1
        assert results[0]['id'] == 123
        assert results[0]['title'] == 'Test MR'
    
    def test_get_branch_mrs_empty_result(self, mr_processor):
        """测试空结果情况"""
        with patch.object(mr_processor, '_get_project_mrs', return_value=[]):
            results = mr_processor.get_branch_mrs('nonexistent-branch')
            assert results == []
```

## 📋 提交规范

### 1. 提交信息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 2. 提交类型

- **feat**: 新功能
- **fix**: Bug 修复
- **docs**: 文档更新
- **style**: 代码格式调整（不影响功能）
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

### 3. 提交示例

```bash
# 新功能
git commit -m "feat(api): add batch validation endpoint"

# Bug 修复
git commit -m "fix(cache): resolve memory leak in file cache"

# 文档更新
git commit -m "docs: update installation guide"

# 重构
git commit -m "refactor(core): simplify validation logic"

# 测试
git commit -m "test: add integration tests for GitLab API"
```

### 4. 提交最佳实践

- 每个提交专注于一个逻辑变更
- 提交信息清晰描述变更内容
- 避免包含无关的格式化变更
- 大的功能分成多个小提交

## 🔍 Pull Request 规范

### 1. PR 标题

使用清晰的标题描述 PR 内容：

```
feat: Add multi-repository validation support
fix: Resolve GitLab API rate limiting issue
docs: Improve configuration documentation
```

### 2. PR 描述模板

```markdown
## 📝 变更摘要

简要描述这个 PR 的主要变更内容。

## 🎯 变更类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新
- [ ] 测试改进
- [ ] 性能优化

## 🧪 测试情况

- [ ] 添加了新的测试
- [ ] 现有测试全部通过
- [ ] 手动测试通过

## 📋 检查清单

- [ ] 代码符合项目规范
- [ ] 添加了必要的文档
- [ ] 更新了相关的配置文件
- [ ] 没有引入新的依赖（或已说明原因）

## 📸 截图（如适用）

添加相关截图或演示图片。

## 🔗 相关 Issue

关闭 #123
相关 #456
```

### 3. PR 审查要求

- 所有 PR 必须通过 CI 检查
- 代码覆盖率不能降低
- 至少需要一个维护者的审查
- 解决所有评论后才能合并

## 🐛 Bug 报告

### 1. Bug 报告模板

```markdown
## 🐛 Bug 描述

清晰描述遇到的问题。

## 🔄 重现步骤

1. 执行命令 `...`
2. 设置配置 `...`
3. 出现错误 `...`

## 🎯 期望行为

描述您期望的正确行为。

## 📱 环境信息

- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- Core Reflow: [e.g. 2.0.0]
- GitLab 版本: [e.g. 15.3.0]

## 📋 额外信息

添加其他相关信息、配置文件、日志等。
```

### 2. Bug 分类

- **Critical**: 系统崩溃、数据丢失
- **High**: 核心功能无法使用
- **Medium**: 功能异常但有变通方案
- **Low**: 界面问题、小的不便

## 💡 功能请求

### 1. 功能请求模板

```markdown
## 🚀 功能描述

简要描述您希望添加的功能。

## 🎯 解决的问题

这个功能解决了什么问题？

## 💭 建议的解决方案

描述您认为可行的实现方案。

## 🔄 替代方案

是否考虑过其他实现方式？

## 📋 额外信息

添加其他相关信息或参考资料。
```

## 📚 文档贡献

### 1. 文档类型

- **用户文档**: 面向最终用户
- **开发者文档**: 面向贡献者
- **API 文档**: 接口说明
- **设计文档**: 架构和设计决策

### 2. 文档规范

- 使用清晰的标题结构
- 提供实用的代码示例
- 包含必要的截图或图表
- 保持内容的时效性

### 3. 文档审查

- 检查语法和拼写
- 验证代码示例的正确性
- 确保链接有效
- 测试操作步骤

## 🏷️ 版本发布

### 1. 版本号规范

使用 [语义化版本](https://semver.org/lang/zh-CN/)：

- **MAJOR.MINOR.PATCH** (例如: 2.1.3)
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的 Bug 修复

### 2. 发布流程

```bash
# 1. 确保所有测试通过
python -m pytest tests/

# 2. 更新版本号和变更日志
./scripts/release.sh --dry-run 2.1.0

# 3. 执行发布
./scripts/release.sh 2.1.0
```

## 🤝 社区准则

### 1. 行为准则

- 尊重所有贡献者
- 提供建设性的反馈
- 专注于技术讨论
- 保持开放和包容的态度

### 2. 沟通渠道

- **GitHub Issues**: Bug 报告和功能请求
- **GitHub Discussions**: 技术讨论和问答
- **Pull Requests**: 代码审查和讨论

### 3. 获得帮助

- 查看 [FAQ](../user_guide/quick_start.md#常见问题)
- 搜索现有的 Issues 和 Discussions
- 创建新的 Issue 描述您的问题
- 参与社区讨论

## 🎉 成为维护者

### 1. 维护者职责

- 审查 Pull Requests
- 管理 Issues 和 Discussions
- 维护代码质量
- 帮助新贡献者

### 2. 成为维护者的条件

- 长期活跃的贡献者
- 熟悉项目架构和目标
- 良好的代码审查能力
- 积极的社区参与

### 3. 联系方式

如果您有兴趣成为维护者，请通过以下方式联系我们：

- 发送邮件到: maintainers@core-reflow.example.com
- 在 GitHub 上 @mention 现有维护者

---

感谢您对 Core Reflow 项目的贡献！每一个贡献都让项目变得更好。🚀

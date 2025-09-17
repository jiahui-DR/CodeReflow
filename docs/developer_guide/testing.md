# 测试指南

本指南详细介绍 Core Reflow 项目的测试策略、测试编写规范和最佳实践。

## 🎯 测试策略

### 测试金字塔

```
        /\
       /  \
      /    \
     /  E2E  \        End-to-End Tests (少量)
    /________\
   /          \
  /Integration \      Integration Tests (适量)
 /______________\
/                \
/   Unit Tests    \    Unit Tests (大量)
/__________________\
```

#### 1. 单元测试 (Unit Tests) - 70%
- 测试单个函数/方法
- 快速执行，独立性强
- 覆盖边界条件和异常情况

#### 2. 集成测试 (Integration Tests) - 20%
- 测试组件间协作
- 验证外部依赖集成
- 包含数据库、API 等

#### 3. 端到端测试 (E2E Tests) - 10%
- 测试完整用户流程
- 验证系统整体功能
- 较慢但覆盖真实场景

## 📁 测试目录结构

```
tests/
├── __init__.py
├── conftest.py                 # pytest 全局配置
├── fixtures/                   # 测试数据
│   ├── __init__.py
│   ├── sample_config.json
│   ├── sample_mrs.json
│   └── sample_commits.json
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_fingerprint_utils.py
│   ├── test_validators.py
│   └── test_parallel.py
├── integration/                # 集成测试
│   ├── __init__.py
│   ├── test_gitlab_api.py
│   ├── test_git_operations.py
│   ├── test_fingerprint_generation.py
│   ├── test_delivery_validation.py
│   └── test_complete_workflow.py
└── e2e/                        # 端到端测试
    ├── __init__.py
    ├── test_cli_interface.py
    └── test_full_validation.py
```

## 🛠️ 测试工具和框架

### 核心工具

- **pytest**: 主测试框架
- **pytest-cov**: 代码覆盖率
- **pytest-mock**: 模拟对象
- **pytest-xdist**: 并行测试
- **pytest-benchmark**: 性能测试

### 安装测试依赖

```bash
pip install pytest pytest-cov pytest-mock pytest-xdist pytest-benchmark
```

### pytest 配置

`pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=core_reflow
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    gitlab_api: Tests requiring GitLab API
    git_repo: Tests requiring Git repository
```

## 📝 单元测试

### 测试类结构

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from core_reflow.utils.cache import MemoryCache


class TestMemoryCache:
    """内存缓存单元测试"""
    
    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return MemoryCache(max_size=10, default_ttl=300)
    
    def test_set_and_get_success(self, cache):
        """测试设置和获取成功情况"""
        # Arrange
        key = "test_key"
        value = "test_value"
        
        # Act
        cache.set(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
    
    def test_get_nonexistent_key(self, cache):
        """测试获取不存在的键"""
        # Act
        result = cache.get("nonexistent")
        
        # Assert
        assert result is None
    
    def test_ttl_expiration(self, cache):
        """测试TTL过期"""
        # Arrange
        key = "expiring_key"
        value = "expiring_value"
        
        # Act
        cache.set(key, value, ttl=0.1)  # 0.1秒过期
        
        # Assert - 立即获取应该成功
        assert cache.get(key) == value
        
        # 等待过期
        import time
        time.sleep(0.2)
        
        # Assert - 过期后应该返回None
        assert cache.get(key) is None
    
    def test_max_size_eviction(self, cache):
        """测试最大容量限制和驱逐策略"""
        # Arrange - 缓存最大容量为10
        
        # Act - 添加11个项目
        for i in range(11):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Assert - 最早的键应该被驱逐
        assert cache.get("key_0") is None
        assert cache.get("key_10") == "value_10"
    
    @pytest.mark.parametrize("key,value,expected", [
        ("string_key", "string_value", "string_value"),
        ("int_key", 42, 42),
        ("list_key", [1, 2, 3], [1, 2, 3]),
        ("dict_key", {"a": 1}, {"a": 1}),
    ])
    def test_different_data_types(self, cache, key, value, expected):
        """测试不同数据类型的存储"""
        cache.set(key, value)
        assert cache.get(key) == expected
```

### Mock 和 Patch 使用

```python
import pytest
from unittest.mock import Mock, patch, call
from core_reflow.gitlab_api.mr_processor import MRProcessor


class TestMRProcessor:
    """MR处理器单元测试"""
    
    @pytest.fixture
    def mock_gitlab(self):
        """模拟GitLab客户端"""
        with patch('core_reflow.gitlab_api.mr_processor.gitlab.Gitlab') as mock:
            yield mock
    
    @pytest.fixture
    def mr_processor(self, mock_gitlab):
        """创建MR处理器实例"""
        return MRProcessor("test-token", "123", "https://gitlab.test.com")
    
    def test_get_branch_mrs_success(self, mr_processor, mock_gitlab):
        """测试成功获取分支MR"""
        # Arrange
        mock_mr = Mock()
        mock_mr.attributes = {
            'id': 123,
            'iid': 45,
            'title': 'Test MR',
            'state': 'merged',
            'source_branch': 'feature/test'
        }
        
        mock_project = Mock()
        mock_project.mergerequests.list.return_value = [mock_mr]
        mock_gitlab.return_value.projects.get.return_value = mock_project
        
        # Act
        results = mr_processor.get_branch_mrs('feature/test')
        
        # Assert
        assert len(results) == 1
        assert results[0]['id'] == 123
        assert results[0]['title'] == 'Test MR'
        
        # 验证API调用
        mock_project.mergerequests.list.assert_called_once_with(
            source_branch='feature/test',
            state='merged',
            all=True
        )
    
    def test_get_branch_mrs_api_error(self, mr_processor, mock_gitlab):
        """测试API错误处理"""
        # Arrange
        from core_reflow.utils.exceptions import GitLabAPIError
        mock_gitlab.return_value.projects.get.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(GitLabAPIError) as exc_info:
            mr_processor.get_branch_mrs('feature/test')
        
        assert "API Error" in str(exc_info.value)
    
    @patch('core_reflow.gitlab_api.mr_processor.time.sleep')
    def test_retry_mechanism(self, mock_sleep, mr_processor, mock_gitlab):
        """测试重试机制"""
        # Arrange
        mock_project = Mock()
        # 前两次调用失败，第三次成功
        mock_project.mergerequests.list.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            []
        ]
        mock_gitlab.return_value.projects.get.return_value = mock_project
        
        # Act
        results = mr_processor.get_branch_mrs('feature/test')
        
        # Assert
        assert results == []
        assert mock_project.mergerequests.list.call_count == 3
        assert mock_sleep.call_count == 2  # 两次重试间隔
```

## 🔗 集成测试

### GitLab API 集成测试

```python
import pytest
import os
from core_reflow.gitlab_api.mr_processor import MRProcessor


@pytest.mark.integration
@pytest.mark.gitlab_api
class TestMRProcessorIntegration:
    """MR处理器集成测试"""
    
    @pytest.fixture(scope="class")
    def real_mr_processor(self):
        """使用真实的GitLab连接"""
        token = os.getenv('GITLAB_TEST_TOKEN')
        project_id = os.getenv('GITLAB_TEST_PROJECT_ID')
        gitlab_url = os.getenv('GITLAB_TEST_URL', 'https://gitlab.com')
        
        if not token or not project_id:
            pytest.skip("Missing GitLab credentials for integration test")
        
        return MRProcessor(token, project_id, gitlab_url)
    
    def test_get_project_info(self, real_mr_processor):
        """测试获取项目信息"""
        # Act
        project = real_mr_processor._get_project()
        
        # Assert
        assert project is not None
        assert hasattr(project, 'name')
        assert hasattr(project, 'id')
    
    def test_get_mrs_from_real_branch(self, real_mr_processor):
        """测试从真实分支获取MR"""
        # 注意：这需要测试项目中有已知的分支
        branch_name = "main"  # 或其他已知存在的分支
        
        # Act
        mrs = real_mr_processor.get_branch_mrs(branch_name)
        
        # Assert
        assert isinstance(mrs, list)
        # 可能为空，取决于实际项目状态
```

### 完整工作流集成测试

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from core_reflow.main import MRReflowValidator


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteWorkflow:
    """完整工作流集成测试"""
    
    @pytest.fixture
    def temp_repo(self):
        """创建临时Git仓库"""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # 初始化Git仓库
        import git
        repo = git.Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "README.md").write_text("# Test Repo")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")
        
        yield repo_path
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def integration_config(self, temp_repo):
        """创建集成测试配置"""
        config = {
            "gitlab": {
                "url": "https://gitlab.test.com",
                "token": "test-token",
                "project_id": "test-project"
            },
            "git": {
                "repo_path": str(temp_repo),
                "target_branch": "main",
                "search_days": 30
            },
            "fingerprint": {
                "ignore_patterns": ["*.md"]
            },
            "performance": {
                "max_workers": 2
            },
            "cache": {
                "backend": "memory",
                "max_size": 100
            }
        }
        
        config_file = temp_repo / "test_config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        return str(config_file)
    
    @patch('core_reflow.gitlab_api.mr_processor.gitlab.Gitlab')
    def test_end_to_end_validation(self, mock_gitlab, integration_config):
        """端到端验证测试"""
        # Arrange - 设置mock响应
        mock_mr = Mock()
        mock_mr.attributes = {
            'id': 123,
            'title': 'Integration Test MR',
            'state': 'merged',
            'source_branch': 'feature/integration-test'
        }
        
        mock_project = Mock()
        mock_project.mergerequests.list.return_value = [mock_mr]
        mock_gitlab.return_value.projects.get.return_value = mock_project
        
        # Act
        validator = MRReflowValidator(integration_config)
        results = validator.validate_branch('feature/integration-test')
        
        # Assert
        assert isinstance(results, list)
        # 其他验证逻辑...
```

## 🚀 端到端测试

### CLI 接口测试

```python
import pytest
import subprocess
import sys
from pathlib import Path


@pytest.mark.e2e
class TestCLIInterface:
    """CLI接口端到端测试"""
    
    def test_cli_help(self):
        """测试CLI帮助信息"""
        # Act
        result = subprocess.run(
            [sys.executable, "-m", "core_reflow.cli", "--help"],
            capture_output=True,
            text=True
        )
        
        # Assert
        assert result.returncode == 0
        assert "Core Reflow CLI" in result.stdout
        assert "--branch" in result.stdout
        assert "--mr-id" in result.stdout
    
    def test_cli_version(self):
        """测试版本信息"""
        # Act
        result = subprocess.run(
            [sys.executable, "-m", "core_reflow.cli", "--version"],
            capture_output=True,
            text=True
        )
        
        # Assert
        assert result.returncode == 0
        assert "2.0.0" in result.stdout  # 或当前版本号
    
    @pytest.mark.skipif(
        not Path("config/config.example.json").exists(),
        reason="Example config not found"
    )
    def test_cli_config_validation(self):
        """测试配置验证"""
        # Act
        result = subprocess.run([
            sys.executable, "-m", "core_reflow.main",
            "--config", "config/config.example.json",
            "--validate-config"
        ], capture_output=True, text=True)
        
        # Assert
        assert result.returncode in [0, 1]  # 配置有效或无效都是预期的
```

## 📊 性能测试

### 基准测试

```python
import pytest
from core_reflow.utils.cache import MemoryCache
from core_reflow.fingerprint.generator import FingerprintGenerator


@pytest.mark.benchmark
class TestPerformance:
    """性能基准测试"""
    
    def test_cache_performance(self, benchmark):
        """测试缓存性能"""
        cache = MemoryCache(max_size=1000)
        
        def cache_operations():
            # 设置操作
            for i in range(100):
                cache.set(f"key_{i}", f"value_{i}")
            
            # 获取操作
            for i in range(100):
                cache.get(f"key_{i}")
        
        # 基准测试
        result = benchmark(cache_operations)
    
    def test_fingerprint_generation_performance(self, benchmark):
        """测试指纹生成性能"""
        generator = FingerprintGenerator()
        
        # 准备测试数据
        changes = []
        for i in range(50):
            changes.append({
                'file_path': f'src/file_{i}.py',
                'content': f'def function_{i}():\n    return {i}\n' * 10,
                'added_lines': 20,
                'deleted_lines': 0
            })
        
        def generate_fingerprints():
            return generator.generate(changes, 123)
        
        # 基准测试
        result = benchmark(generate_fingerprints)
        assert len(result) > 0
    
    @pytest.mark.slow
    def test_parallel_processing_performance(self, benchmark):
        """测试并行处理性能"""
        from core_reflow.utils.parallel import MRParallelProcessor
        
        processor = MRParallelProcessor(max_workers=4)
        
        # 模拟MR列表
        mrs = [{'id': i, 'title': f'MR {i}'} for i in range(20)]
        
        def process_function(mr):
            import time
            time.sleep(0.01)  # 模拟处理时间
            return f"processed_{mr['id']}"
        
        def parallel_processing():
            return processor.process_mrs_parallel(mrs, process_function)
        
        result = benchmark(parallel_processing)
        assert result['success_count'] == 20
```

## 🔧 测试工具和辅助函数

### 自定义 Fixtures

```python
# conftest.py
import pytest
import json
import tempfile
from pathlib import Path


@pytest.fixture
def sample_mr_data():
    """示例MR数据"""
    return {
        'id': 123,
        'iid': 45,
        'title': 'Sample MR',
        'description': 'This is a sample MR for testing',
        'state': 'merged',
        'source_branch': 'feature/sample',
        'target_branch': 'main',
        'merge_commit_sha': 'abcd1234',
        'author': {
            'id': 1,
            'name': 'Test User',
            'username': 'testuser'
        }
    }


@pytest.fixture
def temp_config_file():
    """临时配置文件"""
    config = {
        "gitlab": {
            "url": "https://gitlab.test.com",
            "token": "test-token",
            "project_id": "test-project"
        },
        "git": {
            "repo_path": ".",
            "target_branch": "main"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_file = f.name
    
    yield temp_file
    
    # 清理
    Path(temp_file).unlink()


@pytest.fixture(scope="session")
def test_database():
    """测试数据库会话级fixture"""
    # 设置测试数据库
    db_path = tempfile.mktemp(suffix='.db')
    
    # 初始化数据库
    # ...
    
    yield db_path
    
    # 清理
    if Path(db_path).exists():
        Path(db_path).unlink()
```

### 测试辅助函数

```python
# tests/utils.py
import json
from pathlib import Path
from typing import Dict, Any


def load_test_data(filename: str) -> Dict[str, Any]:
    """加载测试数据文件"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / filename, 'r') as f:
        return json.load(f)


def create_mock_mr(mr_id: int, **kwargs) -> Dict[str, Any]:
    """创建模拟MR数据"""
    default_mr = {
        'id': mr_id,
        'iid': mr_id,
        'title': f'MR {mr_id}',
        'state': 'merged',
        'source_branch': f'feature/mr-{mr_id}',
        'target_branch': 'main'
    }
    default_mr.update(kwargs)
    return default_mr


def assert_mr_result(result: Dict[str, Any], expected_matched: bool):
    """断言MR验证结果"""
    assert 'mr_id' in result
    assert 'matched' in result
    assert 'confidence' in result
    assert isinstance(result['matched'], bool)
    assert isinstance(result['confidence'], (int, float))
    assert 0 <= result['confidence'] <= 1
    assert result['matched'] == expected_matched
```

## 📈 测试覆盖率

### 覆盖率目标

- **整体覆盖率**: ≥ 80%
- **核心模块**: ≥ 90%
- **工具模块**: ≥ 85%
- **API模块**: ≥ 75%

### 覆盖率配置

`.coveragerc`:
```ini
[run]
source = core_reflow
omit = 
    */tests/*
    */venv/*
    */migrations/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

### 运行覆盖率检查

```bash
# 基本覆盖率
pytest --cov=core_reflow

# 详细报告
pytest --cov=core_reflow --cov-report=term-missing

# HTML报告
pytest --cov=core_reflow --cov-report=html

# 覆盖率失败阈值
pytest --cov=core_reflow --cov-fail-under=80
```

## 🚀 运行测试

### 基本运行命令

```bash
# 运行所有测试
pytest

# 运行特定目录
pytest tests/unit/
pytest tests/integration/

# 运行特定文件
pytest tests/unit/test_cache.py

# 运行特定测试
pytest tests/unit/test_cache.py::TestMemoryCache::test_set_and_get

# 按标记运行
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### 并行运行

```bash
# 并行运行测试
pytest -n auto  # 自动检测CPU核心数
pytest -n 4     # 使用4个进程
```

### 详细输出

```bash
# 详细输出
pytest -v

# 显示本地变量
pytest -v --tb=long

# 只显示失败信息
pytest --tb=short

# 停在第一个失败
pytest -x
```

### 特定环境测试

```bash
# 跳过慢速测试
pytest -m "not slow"

# 只运行集成测试
pytest -m integration

# 跳过需要外部依赖的测试
pytest -m "not gitlab_api"
```

## 🏃 持续集成

### GitHub Actions 配置

`.github/workflows/test.yml`:
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-xdist
    
    - name: Run tests
      run: |
        pytest tests/ --cov=core_reflow --cov-report=xml -n auto
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 📚 最佳实践总结

### 1. 测试编写原则

- **FIRST**: Fast, Independent, Repeatable, Self-Validating, Timely
- **AAA**: Arrange, Act, Assert
- **单一职责**: 每个测试只验证一个行为
- **清晰命名**: 测试名称描述被测试的行为

### 2. Mock 使用指导

- 对外部依赖使用 Mock
- 避免过度 Mock 内部实现
- 使用 Mock 验证交互行为
- Mock 的行为要与真实对象一致

### 3. 测试数据管理

- 使用 Fixture 提供测试数据
- 避免测试间的数据依赖
- 使用工厂模式生成测试数据
- 敏感数据使用环境变量

### 4. 性能测试建议

- 建立性能基准
- 监控关键操作的性能
- 使用真实规模的测试数据
- 定期运行性能回归测试

通过遵循这些测试指南和最佳实践，可以确保 Core Reflow 项目的代码质量和稳定性。

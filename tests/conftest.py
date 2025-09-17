"""
pytest 配置文件 - 为所有测试提供共享的fixture和配置
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_reflow.utils.config import ConfigManager
from core_reflow.utils.cache import MemoryCache, CacheManager
from core_reflow.gitlab_api.mr_processor import MRProcessor
from core_reflow.git_operations.extractor import ChangeExtractor
from core_reflow.fingerprint.generator import FingerprintGenerator


@pytest.fixture(scope="session")
def fixtures_dir():
    """返回测试数据目录路径"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_config_data(fixtures_dir):
    """加载示例配置数据"""
    config_file = fixtures_dir / "sample_config.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sample_mrs_data(fixtures_dir):
    """加载示例MR数据"""
    mrs_file = fixtures_dir / "sample_mrs.json"
    with open(mrs_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_file(temp_dir, sample_config_data):
    """创建临时配置文件"""
    config_file = temp_dir / "test_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config_data, f, indent=2)
    return config_file


@pytest.fixture
def config_manager(temp_config_file):
    """配置管理器实例"""
    return ConfigManager(str(temp_config_file))


@pytest.fixture
def memory_cache():
    """内存缓存实例"""
    return MemoryCache(max_size=100, default_ttl=300)


@pytest.fixture
def cache_manager(memory_cache):
    """缓存管理器实例"""
    return CacheManager(memory_cache)


@pytest.fixture
def mock_gitlab_client():
    """模拟GitLab客户端"""
    mock_client = Mock()
    
    # 模拟项目获取
    mock_client.projects.get.return_value = Mock(
        id=42,
        name="test-project",
        web_url="https://gitlab.test.com/group/test-project"
    )
    
    # 模拟MR列表
    mock_mr_1 = Mock()
    mock_mr_1.attributes = {
        'id': 123,
        'iid': 45,
        'title': 'Add user authentication feature',
        'state': 'merged',
        'source_branch': 'feature/auth-system',
        'target_branch': 'dev_master',
        'merge_commit_sha': 'a1b2c3d4e5f6'
    }
    
    mock_mr_2 = Mock()
    mock_mr_2.attributes = {
        'id': 124,
        'iid': 46,
        'title': 'Fix database connection timeout',
        'state': 'merged',
        'source_branch': 'bugfix/db-timeout',
        'target_branch': 'dev_master',
        'merge_commit_sha': 'f6e5d4c3b2a1'
    }
    
    mock_client.projects.get().mergerequests.list.return_value = [mock_mr_1, mock_mr_2]
    mock_client.projects.get().mergerequests.get.return_value = mock_mr_1
    
    return mock_client


@pytest.fixture
def mock_mr_processor(mock_gitlab_client, sample_mrs_data):
    """模拟MR处理器"""
    processor = MRProcessor("test-token", "42", "https://gitlab.test.com")
    processor._gitlab = mock_gitlab_client
    
    # 模拟获取分支MR
    def mock_get_branch_mrs(branch_name):
        return sample_mrs_data["sample_mrs"][:2]  # 返回前两个MR
    
    # 模拟获取单个MR
    def mock_get_mr_by_id(mr_id):
        for mr in sample_mrs_data["sample_mrs"]:
            if mr["id"] == mr_id:
                return mr
        return None
    
    processor.get_branch_mrs = mock_get_branch_mrs
    processor.get_mr_by_id = mock_get_mr_by_id
    
    return processor


@pytest.fixture
def mock_git_repo():
    """模拟Git仓库"""
    mock_repo = Mock()
    
    # 模拟提交
    mock_commit = Mock()
    mock_commit.hexsha = "a1b2c3d4e5f6"
    mock_commit.committed_date = 1705420800  # 2024-01-16 14:20:00 UTC
    mock_commit.message = "Add user authentication feature"
    mock_commit.stats.files = {
        "src/auth/login.py": {"insertions": 8, "deletions": 1, "lines": 9}
    }
    
    # 模拟分支
    mock_branch = Mock()
    mock_branch.name = "dev_master"
    mock_branch.commit = mock_commit
    
    mock_repo.heads = [mock_branch]
    mock_repo.iter_commits.return_value = [mock_commit]
    mock_repo.git.show.return_value = """
diff --git a/src/auth/login.py b/src/auth/login.py
index 1234567..abcdefg 100644
--- a/src/auth/login.py
+++ b/src/auth/login.py
@@ -1,3 +1,10 @@
+def authenticate_user(username, password):
+    \"\"\"验证用户登录\"\"\"
+    return oauth_client.verify_credentials(username, password)
+
 def login(request):
     username = request.get('username')
     password = request.get('password')
+    if authenticate_user(username, password):
+        return create_session(username)
+    return None
"""
    
    return mock_repo


@pytest.fixture
def mock_change_extractor(mock_git_repo, sample_mrs_data):
    """模拟变更提取器"""
    extractor = ChangeExtractor("/tmp/test-repo")
    
    def mock_extract_changes(mr):
        # 返回示例MR的变更数据
        return mr.get("changes", [])
    
    extractor.extract_changes = mock_extract_changes
    return extractor


@pytest.fixture
def mock_fingerprint_generator(sample_mrs_data):
    """模拟指纹生成器"""
    generator = FingerprintGenerator([])
    
    def mock_generate(changes, mr_id):
        # 返回对应MR的指纹数据
        for fp_data in sample_mrs_data["sample_fingerprints"]:
            if fp_data["mr_id"] == mr_id:
                return fp_data["fingerprints"]
        return []
    
    generator.generate = mock_generate
    return generator


@pytest.fixture
def sample_validation_results():
    """示例验证结果"""
    return [
        {
            "mr_id": 123,
            "fingerprint_id": "sha256:a1b2c3d4e5f6g7h8i9j0",
            "matched": True,
            "confidence": 0.98,
            "match_details": {
                "commit_sha": "a1b2c3d4e5f6",
                "file_path": "src/auth/login.py",
                "similarity": 0.98
            }
        },
        {
            "mr_id": 124,
            "fingerprint_id": "sha256:f6e5d4c3b2a1z9y8x7w6",
            "matched": True,
            "confidence": 1.0,
            "match_details": {
                "commit_sha": "f6e5d4c3b2a1",
                "file_path": "src/database/connection.py",
                "similarity": 1.0
            }
        }
    ]


# pytest 配置
def pytest_configure(config):
    """pytest 配置"""
    # 添加自定义标记
    config.addinivalue_line("markers", "slow: 标记为慢速测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "gitlab_api: 需要GitLab API的测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试添加默认标记
    for item in items:
        # 根据文件路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 为包含 "gitlab" 的测试添加 gitlab_api 标记
        if "gitlab" in item.name.lower() or "gitlab" in str(item.fspath):
            item.add_marker(pytest.mark.gitlab_api)


# 全局测试配置
pytest_plugins = []

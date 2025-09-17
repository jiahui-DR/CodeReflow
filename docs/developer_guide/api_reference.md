# API 参考文档

本文档详细介绍 Core Reflow 系统的编程接口，包括所有主要类、方法和函数的详细说明。

## 📚 模块概览

### 核心模块
- [`core_reflow.main`](#main-module) - 主入口和核心验证器
- [`core_reflow.core`](#core-module) - 核心业务逻辑
- [`core_reflow.utils`](#utils-module) - 工具和基础设施

### 集成模块
- [`core_reflow.gitlab_api`](#gitlab-api-module) - GitLab API 集成
- [`core_reflow.git_operations`](#git-operations-module) - Git 操作
- [`core_reflow.fingerprint`](#fingerprint-module) - 指纹生成

## 🎯 Main Module

### MRReflowValidator

主要的 MR 回流验证器类。

```python
class MRReflowValidator:
    """MR回流验证器"""
    
    def __init__(self, config_file: str = None) -> None:
        """
        初始化验证器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
            
        Raises:
            ConfigurationError: 配置加载失败时抛出
        """
```

#### 方法

##### validate_branch()

```python
def validate_branch(self, branch_name: str) -> List[Dict[str, Any]]:
    """
    验证指定分支的所有MR
    
    Args:
        branch_name: 分支名称
        
    Returns:
        验证结果列表，每个元素包含：
        - mr_id: MR ID
        - title: MR 标题
        - matched: 是否匹配 (bool)
        - confidence: 匹配置信度 (float, 0-1)
        - match_details: 匹配详情 (dict)
        
    Raises:
        ValidationError: 验证过程失败时抛出
        
    Example:
        >>> validator = MRReflowValidator('config.json')
        >>> results = validator.validate_branch('feature/auth')
        >>> for result in results:
        ...     print(f"MR #{result['mr_id']}: {result['matched']}")
    """
```

##### validate_mr()

```python
def validate_mr(self, mr_id: int) -> List[Dict[str, Any]]:
    """
    验证指定MR
    
    Args:
        mr_id: MR ID
        
    Returns:
        验证结果列表
        
    Raises:
        ValidationError: 验证失败时抛出
        
    Example:
        >>> validator = MRReflowValidator()
        >>> results = validator.validate_mr(123)
        >>> print(f"匹配状态: {results[0]['matched']}")
    """
```

## 🔧 Core Module

### DeliveryBranchValidator

交付分支验证器，专门用于验证交付分支的 MR 回流情况。

```python
class DeliveryBranchValidator:
    """交付分支验证器"""
    
    def __init__(self, config_file: str = None) -> None:
        """
        初始化交付分支验证器
        
        Args:
            config_file: 配置文件路径
        """
```

#### 方法

##### validate_delivery_branch()

```python
def validate_delivery_branch(self, delivery_branch: str) -> Dict[str, Any]:
    """
    验证交付分支
    
    Args:
        delivery_branch: 交付分支名称
        
    Returns:
        验证报告，包含：
        - branch_name: 分支名称
        - total_mrs: 总MR数量
        - validated_mrs: 已验证MR数量
        - unvalidated_mrs: 未验证MR列表
        - validation_rate: 验证率
        
    Example:
        >>> validator = DeliveryBranchValidator()
        >>> report = validator.validate_delivery_branch('delivery/v1.0.0')
        >>> print(f"验证率: {report['validation_rate']:.2%}")
    """
```

### MatchValidator

匹配结果验证器，负责验证搜索结果的质量。

```python
class MatchValidator:
    """匹配结果验证器"""
    
    def __init__(self, similarity_threshold: float = 0.8) -> None:
        """
        初始化验证器
        
        Args:
            similarity_threshold: 相似度阈值
        """
```

#### 方法

##### validate_results()

```python
def validate_results(self, search_results: List[Dict]) -> List[Dict]:
    """
    验证搜索结果
    
    Args:
        search_results: 搜索结果列表
        
    Returns:
        验证后的结果列表
        
    Example:
        >>> validator = MatchValidator(similarity_threshold=0.9)
        >>> results = validator.validate_results(search_results)
    """
```

### ResultOutputer

结果输出器，负责格式化和输出验证结果。

```python
class ResultOutputer:
    """结果输出器"""
    
    def __init__(self) -> None:
        """初始化输出器"""
```

#### 方法

##### output_results()

```python
def output_results(self, results: List[Dict], format_type: str = 'console') -> str:
    """
    输出验证结果
    
    Args:
        results: 验证结果列表
        format_type: 输出格式 ('console', 'json', 'markdown')
        
    Returns:
        格式化后的输出字符串
        
    Example:
        >>> outputer = ResultOutputer()
        >>> output = outputer.output_results(results, 'json')
        >>> print(output)
    """
```

## 📡 GitLab API Module

### MRProcessor

GitLab MR 处理器，封装 GitLab API 调用。

```python
class MRProcessor:
    """GitLab MR 处理器"""
    
    def __init__(self, token: str, project_id: str, gitlab_url: str = 'https://gitlab.com') -> None:
        """
        初始化MR处理器
        
        Args:
            token: GitLab 访问令牌
            project_id: 项目 ID
            gitlab_url: GitLab 服务器 URL
            
        Raises:
            GitLabAPIError: API 连接失败时抛出
        """
```

#### 方法

##### get_branch_mrs()

```python
def get_branch_mrs(self, branch_name: str, state: str = 'merged') -> List[Dict]:
    """
    获取指定分支的MR列表
    
    Args:
        branch_name: 分支名称
        state: MR 状态 ('opened', 'closed', 'merged', 'all')
        
    Returns:
        MR 列表，每个元素包含：
        - id: MR ID
        - iid: 项目内 ID
        - title: 标题
        - description: 描述
        - source_branch: 源分支
        - target_branch: 目标分支
        - merge_commit_sha: 合并提交 SHA
        - created_at: 创建时间
        - merged_at: 合并时间
        - author: 作者信息
        
    Raises:
        GitLabAPIError: API 调用失败时抛出
        
    Example:
        >>> processor = MRProcessor(token, project_id)
        >>> mrs = processor.get_branch_mrs('feature/auth')
        >>> print(f"找到 {len(mrs)} 个MR")
    """
```

##### get_mr_by_id()

```python
def get_mr_by_id(self, mr_id: int) -> Dict:
    """
    根据ID获取MR详情
    
    Args:
        mr_id: MR ID
        
    Returns:
        MR 详情字典
        
    Raises:
        GitLabAPIError: MR 不存在或API调用失败
        
    Example:
        >>> mr = processor.get_mr_by_id(123)
        >>> print(f"MR 标题: {mr['title']}")
    """
```

##### get_mr_changes()

```python
def get_mr_changes(self, mr_id: int) -> List[Dict]:
    """
    获取MR的文件变更列表
    
    Args:
        mr_id: MR ID
        
    Returns:
        文件变更列表，每个元素包含：
        - old_path: 旧文件路径
        - new_path: 新文件路径
        - diff: 差异内容
        - new_file: 是否为新文件
        - renamed_file: 是否为重命名文件
        - deleted_file: 是否为删除文件
        
    Example:
        >>> changes = processor.get_mr_changes(123)
        >>> for change in changes:
        ...     print(f"文件: {change['new_path']}")
    """
```

## 📁 Git Operations Module

### ChangeExtractor

Git 变更提取器，从 Git 仓库中提取代码变更。

```python
class ChangeExtractor:
    """Git 变更提取器"""
    
    def __init__(self, repo_path: str) -> None:
        """
        初始化变更提取器
        
        Args:
            repo_path: Git 仓库路径
            
        Raises:
            GitOperationError: 仓库路径无效或不是Git仓库
        """
```

#### 方法

##### extract_changes()

```python
def extract_changes(self, mr: Dict) -> List[Dict]:
    """
    从MR中提取代码变更
    
    Args:
        mr: MR 信息字典
        
    Returns:
        变更列表，每个元素包含：
        - file_path: 文件路径
        - content: 变更内容
        - added_lines: 新增行数
        - deleted_lines: 删除行数
        - change_type: 变更类型 ('added', 'modified', 'deleted')
        
    Example:
        >>> extractor = ChangeExtractor('/path/to/repo')
        >>> changes = extractor.extract_changes(mr)
        >>> print(f"提取到 {len(changes)} 个变更")
    """
```

### MasterBranchSearcher

主线分支搜索器，在主线分支中搜索匹配的代码变更。

```python
class MasterBranchSearcher:
    """主线分支搜索器"""
    
    def __init__(self, repo_path: str, target_branch: str, 
                 cache_manager: CacheManager = None,
                 ignore_patterns: List[str] = None) -> None:
        """
        初始化搜索器
        
        Args:
            repo_path: Git 仓库路径
            target_branch: 目标分支名称
            cache_manager: 缓存管理器
            ignore_patterns: 忽略文件模式列表
        """
```

#### 方法

##### search_changes_in_master()

```python
def search_changes_in_master(self, fingerprints: List[Dict], 
                           search_days: int = 30) -> List[Dict]:
    """
    在主线分支中搜索变更
    
    Args:
        fingerprints: 指纹列表
        search_days: 搜索天数范围
        
    Returns:
        搜索结果列表，每个元素包含：
        - fingerprint_id: 指纹ID
        - matches: 匹配结果列表
        - confidence: 匹配置信度
        
    Example:
        >>> searcher = MasterBranchSearcher('/path/to/repo', 'main')
        >>> results = searcher.search_changes_in_master(fingerprints, 30)
    """
```

## 🔍 Fingerprint Module

### FingerprintGenerator

指纹生成器，为代码变更生成唯一指纹。

```python
class FingerprintGenerator:
    """指纹生成器"""
    
    def __init__(self, ignore_patterns: List[str] = None) -> None:
        """
        初始化指纹生成器
        
        Args:
            ignore_patterns: 忽略文件模式列表
        """
```

#### 方法

##### generate()

```python
def generate(self, changes: List[Dict], mr_id: int) -> List[Dict]:
    """
    为变更列表生成指纹
    
    Args:
        changes: 变更列表
        mr_id: MR ID
        
    Returns:
        指纹列表，每个元素包含：
        - id: 指纹ID
        - mr_id: 关联MR ID
        - file_path: 文件路径
        - content_hash: 内容哈希
        - metadata: 元数据字典
        
    Example:
        >>> generator = FingerprintGenerator(['*.md', '*.txt'])
        >>> fingerprints = generator.generate(changes, 123)
        >>> print(f"生成 {len(fingerprints)} 个指纹")
    """
```

## 🛠️ Utils Module

### ConfigManager

配置管理器，负责加载和管理系统配置。

```python
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None) -> None:
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
            
        Raises:
            ConfigurationError: 配置文件加载失败
        """
```

#### 方法

##### get()

```python
def get(self, key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键，支持点号分隔的路径 (如: 'gitlab.token')
        default: 默认值
        
    Returns:
        配置值
        
    Example:
        >>> config = ConfigManager('config.json')
        >>> token = config.get('gitlab.token')
        >>> workers = config.get('performance.max_workers', 4)
    """
```

##### set()

```python
def set(self, key: str, value: Any) -> None:
    """
    设置配置值
    
    Args:
        key: 配置键
        value: 配置值
        
    Example:
        >>> config.set('performance.max_workers', 8)
    """
```

##### validate()

```python
def validate(self) -> bool:
    """
    验证配置有效性
    
    Returns:
        是否有效
        
    Example:
        >>> if not config.validate():
        ...     print("配置无效")
    """
```

### CacheManager

缓存管理器，提供统一的缓存接口。

```python
class CacheManager:
    """缓存管理器"""
    
    def __init__(self, backend: CacheBackend) -> None:
        """
        初始化缓存管理器
        
        Args:
            backend: 缓存后端实现
        """
```

#### 方法

##### get()

```python
def get(self, key: str) -> Any:
    """
    获取缓存值
    
    Args:
        key: 缓存键
        
    Returns:
        缓存值，如果不存在返回None
        
    Example:
        >>> cache = CacheManager(MemoryCache())
        >>> value = cache.get('user:123')
    """
```

##### set()

```python
def set(self, key: str, value: Any, ttl: int = None) -> None:
    """
    设置缓存值
    
    Args:
        key: 缓存键
        value: 缓存值
        ttl: 生存时间（秒）
        
    Example:
        >>> cache.set('user:123', user_data, ttl=3600)
    """
```

##### get_stats()

```python
def get_stats(self) -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        统计信息字典，包含：
        - hit_rate: 命中率
        - miss_rate: 未命中率
        - size: 当前大小
        - max_size: 最大大小
        
    Example:
        >>> stats = cache.get_stats()
        >>> print(f"命中率: {stats['hit_rate']:.2%}")
    """
```

### MRParallelProcessor

MR 并行处理器，提供高效的并行处理能力。

```python
class MRParallelProcessor:
    """MR 并行处理器"""
    
    def __init__(self, max_workers: int = 4) -> None:
        """
        初始化并行处理器
        
        Args:
            max_workers: 最大工作线程数
        """
```

#### 方法

##### process_mrs_parallel()

```python
def process_mrs_parallel(self, mrs: List[Dict], 
                        processor_func: Callable,
                        progress_callback: Callable = None) -> Dict[str, Any]:
    """
    并行处理MR列表
    
    Args:
        mrs: MR 列表
        processor_func: 处理函数，接受单个MR作为参数
        progress_callback: 进度回调函数
        
    Returns:
        处理结果字典，包含：
        - results: 结果列表
        - success_count: 成功数量
        - error_count: 错误数量
        - duration: 处理耗时
        
    Example:
        >>> processor = MRParallelProcessor(max_workers=8)
        >>> def process_mr(mr):
        ...     return validate_single_mr(mr)
        >>> result = processor.process_mrs_parallel(mrs, process_mr)
        >>> print(f"处理成功: {result['success_count']}")
    """
```

## 🚨 异常类

### CoreReflowError

```python
class CoreReflowError(Exception):
    """Core Reflow 基础异常类"""
    pass
```

### ConfigurationError

```python
class ConfigurationError(CoreReflowError):
    """配置相关异常"""
    pass
```

### GitLabAPIError

```python
class GitLabAPIError(CoreReflowError):
    """GitLab API 相关异常"""
    
    def __init__(self, message: str, status_code: int = None, response: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
```

### GitOperationError

```python
class GitOperationError(CoreReflowError):
    """Git 操作相关异常"""
    pass
```

### ValidationError

```python
class ValidationError(CoreReflowError):
    """验证相关异常"""
    pass
```

## 📝 使用示例

### 基础使用

```python
from core_reflow.main import MRReflowValidator

# 初始化验证器
validator = MRReflowValidator('config.json')

# 验证分支
results = validator.validate_branch('feature/auth')

# 处理结果
for result in results:
    if result['matched']:
        print(f"✅ MR #{result['mr_id']}: 已找到匹配")
    else:
        print(f"❌ MR #{result['mr_id']}: 未找到匹配")
```

### 自定义处理

```python
from core_reflow.gitlab_api.mr_processor import MRProcessor
from core_reflow.git_operations.extractor import ChangeExtractor
from core_reflow.fingerprint.generator import FingerprintGenerator

# 自定义处理流程
mr_processor = MRProcessor(token, project_id)
change_extractor = ChangeExtractor('/path/to/repo')
fingerprint_gen = FingerprintGenerator(['*.md'])

# 获取MR
mrs = mr_processor.get_branch_mrs('feature/test')

# 处理每个MR
for mr in mrs:
    changes = change_extractor.extract_changes(mr)
    fingerprints = fingerprint_gen.generate(changes, mr['id'])
    print(f"MR #{mr['id']}: {len(fingerprints)} 个指纹")
```

### 缓存使用

```python
from core_reflow.utils.cache import CacheManager, MemoryCache

# 设置缓存
cache_backend = MemoryCache(max_size=1000, default_ttl=3600)
cache_manager = CacheManager(cache_backend)

# 使用缓存
cache_key = f"mr_changes:{mr_id}"
changes = cache_manager.get(cache_key)

if changes is None:
    changes = extract_changes_from_git(mr)
    cache_manager.set(cache_key, changes)

print(f"缓存命中率: {cache_manager.get_stats()['hit_rate']:.2%}")
```

## 🔗 相关资源

- [快速开始指南](../user_guide/quick_start.md)
- [配置指南](../user_guide/configuration.md)
- [系统架构](architecture.md)
- [贡献指南](contributing.md)

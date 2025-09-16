# API文档和扩展说明

## API 参考

### MRProcessor 类

#### 方法：`get_branch_mrs(source_branch, target_branch='dev_master')`

获取指定分支的MR列表

**参数**：
- `source_branch` (str): 源分支名称
- `target_branch` (str): 目标分支名称，默认为 'dev_master'

**返回值**：
```python
[
    {
        'id': 123,
        'title': 'Fix user authentication bug',
        'description': 'Fixed authentication issue...',
        'source_branch': 'feature/auth-fix',
        'target_branch': 'dev_master',
        'merge_commit_sha': 'a1b2c3d4...',
        'state': 'merged',
        'author': 'john.doe'
    }
]
```

### ChangeExtractor 类

#### 方法：`extract_changes(mr_info)`

从MR信息中提取代码变更

**参数**：
- `mr_info` (dict): MR信息字典

**返回值**：
```python
[
    {
        'file_path': 'src/service/user.py',
        'change_type': 'MODIFY',
        'diff_content': '@@ -10,5 +10,7 @@\n-    return None\n+    return user_data\n+    if not user_data:\n+        return None\n'
    }
]
```

### FingerprintGenerator 类

#### 方法：`generate(changes)`

为代码变更生成指纹

**参数**：
- `changes` (list): 变更列表

**返回值**：
```python
[
    {
        'fingerprint': 'a1b2c3d4e5f67890',
        'mr_id': 123,
        'file_path': 'src/service/user.py',
        'change_type': 'MODIFY',
        'line_count': 3,
        'content_preview': 'return user_data\nif not user_data:\nreturn None'
    }
]
```

### MasterBranchSearcher 类

#### 方法：`search_changes_in_master(mr_fingerprints, days_back=30)`

在主线分支中搜索MR变更的匹配

**参数**：
- `mr_fingerprints` (list): MR指纹列表
- `days_back` (int): 搜索时间范围（天），默认为30天

**返回值**：
```python
[
    {
        'mr_id': 123,
        'fingerprint': 'a1b2c3d4e5f67890',
        'file_path': 'src/service/user.py',
        'matched': true,
        'match_commit': 'b2c3d4e5f678901234567890abcdef12345678',
        'match_type': 'direct_merge',
        'confidence': 1.0
    }
]
```

### MatchValidator 类

#### 方法：`validate_results(search_results)`

验证搜索结果并生成最终结论

**参数**：
- `search_results` (list): 搜索结果列表

**返回值**：
```python
[
    {
        'mr_id': 123,
        'fingerprint': 'a1b2c3d4e5f67890',
        'file_path': 'src/service/user.py',
        'matched': true,
        'match_commit': 'b2c3d4e5f678901234567890abcdef12345678',
        'match_type': 'direct_merge',
        'confidence': 1.0,
        'conclusion': '已进入主线',
        'reason': '通过直接合并进入主线分支，匹配提交: b2c3d4e5',
        'recommendation': '无需操作'
    }
]
```

### ResultOutputer 类

#### 方法：`output_results(validated_results, output_format='console')`

输出验证结果

**参数**：
- `validated_results` (list): 验证结果列表
- `output_format` (str): 输出格式 ('console', 'json', 'markdown')

## 配置说明

### GitLab配置

```json
{
  "gitlab": {
    "url": "https://gitlab.yourcompany.com",
    "token": "your-personal-access-token",
    "project_id": 12345
  }
}
```

### Git配置

```json
{
  "git": {
    "repo_path": "/absolute/path/to/git/repository",
    "target_branch": "dev_master",
    "search_days": 30
  }
}
```

### 指纹配置

```json
{
  "fingerprint": {
    "ignore_patterns": [
      "^\\s*#.*$",           # 注释行
      "^\\s*$",              # 空行
      "^\\s*import",         # 导入语句
      "^\\s*from.*import"    # 导入语句
    ]
  }
}
```

## 扩展说明

### 支持的合并场景

1. **直接合并 (Direct Merge)**
   - MR直接合并到目标分支
   - 置信度：1.0

2. **Cherry-pick**
   - 变更被cherry-pick到目标分支
   - 置信度：0.9

3. **多路径合并**
   - 通过中间分支间接合并
   - 置信度：0.9

4. **代码重构**
   - 代码逻辑等价但形式不同
   - 置信度：0.5-0.8（需要人工确认）

### 性能优化

1. **缓存策略**
   - 缓存最近的提交指纹
   - 缓存分支合并历史

2. **并行处理**
   - 多线程处理多个MR
   - 分布式处理大规模仓库

3. **增量验证**
   - 只验证新增的变更
   - 跳过已验证的MR

### 错误处理

1. **网络错误**
   - GitLab API调用失败时的重试机制
   - 超时处理

2. **Git操作错误**
   - 仓库访问权限问题
   - 分支不存在的情况

3. **数据一致性**
   - MR状态变更时的处理
   - 并发访问控制

### 扩展功能

1. **多语言支持**
   - JavaScript/TypeScript
   - Java
   - C++
   - Go

2. **高级匹配算法**
   - AST语法树分析
   - 语义相似度计算
   - 机器学习辅助匹配

3. **可视化界面**
   - Web界面展示结果
   - 交互式分支图
   - 统计报表

4. **集成能力**
   - CI/CD Pipeline集成
   - Slack/Teams通知
   - Jira问题跟踪

## 故障排除

### 常见问题

1. **GitLab Token权限不足**
   - 确保Token有读取MR和仓库的权限
   - 检查项目访问权限

2. **Git仓库路径错误**
   - 使用绝对路径
   - 确保有读取权限

3. **分支不存在**
   - 检查分支名称拼写
   - 确认分支已推送到远程

4. **性能问题**
   - 调整search_days参数
   - 启用缓存机制

### 日志分析

系统会输出详细的日志信息，帮助诊断问题：

```
2024-01-15 10:30:15 INFO - Processing MR #123
2024-01-15 10:30:16 INFO - Generated 5 fingerprints for MR #123
2024-01-15 10:30:17 INFO - Found match in commit a1b2c3d4
2024-01-15 10:30:17 INFO - Validation completed for MR #123
```

### 调试模式

启用调试模式获取更详细的信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 版本历史

- **v0.1.0**: 基础功能实现
  - MR获取和处理
  - 基础指纹生成
  - 简单匹配验证

- **v0.2.0**: 性能优化
  - 缓存机制
  - 并行处理
  - 增量验证

- **v1.0.0**: 生产就绪
  - 多语言支持
  - 高级匹配算法
  - Web界面

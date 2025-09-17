# 快速开始指南

欢迎使用 Core Reflow！本指南将帮助您快速上手 MR 回流验证系统。

## 🎯 Core Reflow 是什么？

Core Reflow 是一个 **MR（Merge Request）回流验证系统**，用于验证 GitLab 中的合并请求是否已经成功进入主线分支。

### 主要功能

- ✅ **MR 回流验证**: 检查特定分支的 MR 是否已进入主线
- 🚀 **批量处理**: 支持并行处理多个 MR，提高效率
- 📊 **详细报告**: 生成全面的验证报告和统计信息
- 🔄 **交付分支验证**: 专门针对交付分支的验证功能
- 🏢 **多仓库支持**: 同时验证多个仓库的 MR 状态

## 🚀 第一次使用

### 1. 交互式配置

如果您是第一次使用，建议使用交互式配置向导：

```bash
core-reflow-cli --interactive
```

这将引导您完成以下配置：
- GitLab 服务器信息和访问令牌
- Git 仓库路径和目标分支
- 输出格式和性能设置

### 2. 基础配置示例

您也可以手动创建配置文件 `config.json`：

```json
{
  "gitlab": {
    "url": "https://gitlab.example.com",
    "token": "your-gitlab-token",
    "project_id": "123"
  },
  "git": {
    "repo_path": "/path/to/your/repo",
    "target_branch": "dev_master",
    "search_days": 30
  },
  "output": {
    "format": "console"
  }
}
```

## 📝 基本使用方法

### 验证单个分支

验证指定分支的所有 MR：

```bash
# 使用默认配置
core-reflow --branch feature/user-auth

# 使用自定义配置文件
core-reflow --branch feature/user-auth --config my-config.json

# 指定搜索时间范围
core-reflow --branch feature/user-auth --days 60
```

### 验证单个 MR

验证特定的 MR：

```bash
# 验证 MR #123
core-reflow --mr-id 123

# 生成 JSON 格式报告
core-reflow --mr-id 123 --output json
```

### 验证交付分支

验证交付分支的 MR 是否都已进入主线：

```bash
# 验证交付分支
core-reflow-cli --delivery-branch delivery/v1.0.0

# 使用自定义配置
core-reflow-cli --delivery-branch delivery/v1.0.0 --config delivery-config.json
```

## 📊 输出格式

### 控制台输出（默认）

```
🔍 开始验证分支: feature/user-auth
1. 获取MR列表...
找到 3 个MR

2. 并行处理MR变更...
处理进度: 1/3 (33.3%) - MR #123
处理进度: 2/3 (66.7%) - MR #124
处理进度: 3/3 (100.0%) - MR #125

3. 生成验证报告...

=== 验证结果 ===
✅ MR #123: Add user authentication - 已找到匹配 (98.5% 相似度)
✅ MR #124: Fix database timeout - 已找到匹配 (100.0% 相似度)
❌ MR #125: Update documentation - 未找到匹配

=== 验证统计信息 ===
并行处理统计:
  - 成功处理: 3
  - 处理失败: 0
验证结果统计:
  - 总结果数: 3
  - 匹配成功: 2
  - 匹配失败: 1
  - 匹配率: 66.7%
```

### JSON 输出

```bash
core-reflow --branch feature/user-auth --output json
```

```json
{
  "validation_results": [
    {
      "mr_id": 123,
      "title": "Add user authentication",
      "matched": true,
      "confidence": 0.985,
      "match_details": {
        "commit_sha": "a1b2c3d4",
        "file_path": "src/auth/login.py",
        "similarity": 0.985
      }
    }
  ],
  "statistics": {
    "total_mrs": 3,
    "matched": 2,
    "unmatched": 1,
    "match_rate": 0.667
  }
}
```

### Markdown 输出

```bash
core-reflow --branch feature/user-auth --output markdown > report.md
```

## 🔧 常用配置选项

### 性能优化

```bash
# 增加并行工作线程
core-reflow --branch feature/new --workers 8

# 启用详细性能指标
core-reflow --branch feature/new --metrics

# 清空缓存后运行
core-reflow --branch feature/new --cache-clear
```

### 搜索优化

```bash
# 缩短搜索时间范围（提高速度）
core-reflow --branch feature/new --days 7

# 延长搜索时间范围（更全面）
core-reflow --branch feature/new --days 90
```

## 🏢 多仓库验证

对于需要验证多个仓库的场景，可以使用多仓库配置：

### 1. 创建多仓库配置文件

`delivery_config.json`:
```json
{
  "repositories": [
    {
      "name": "Backend API",
      "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "your-token",
        "project_id": "123"
      },
      "git": {
        "repo_path": "/path/to/backend",
        "target_branch": "dev_master"
      },
      "delivery_branches": ["delivery/v1.0.0"]
    },
    {
      "name": "Frontend App",
      "gitlab": {
        "url": "https://gitlab.example.com", 
        "token": "your-token",
        "project_id": "456"
      },
      "git": {
        "repo_path": "/path/to/frontend",
        "target_branch": "main"
      },
      "delivery_branches": ["delivery/v2.0.0"]
    }
  ]
}
```

### 2. 执行多仓库验证

```bash
core-reflow-cli --multi-repo delivery_config.json
```

## 💡 实用技巧

### 1. 配置模板

查看配置文件示例：
```bash
# 单仓库配置示例
core-reflow-cli --config-example single

# 多仓库配置示例  
core-reflow-cli --config-example delivery
```

### 2. 环境变量

设置常用的环境变量：
```bash
export GITLAB_TOKEN="your-gitlab-token"
export GITLAB_URL="https://gitlab.example.com"
export CORE_REFLOW_CONFIG="/path/to/config.json"
```

### 3. 批处理脚本

创建批处理脚本 `validate_all.sh`：
```bash
#!/bin/bash
echo "验证所有功能分支..."

branches=("feature/auth" "feature/payment" "feature/notification")

for branch in "${branches[@]}"; do
    echo "验证分支: $branch"
    core-reflow --branch "$branch" --config production-config.json
    echo "---"
done

echo "所有分支验证完成！"
```

## 📈 性能监控

启用详细的性能监控：

```bash
core-reflow --branch feature/large --metrics --workers 4
```

输出示例：
```
📊 详细性能指标:
  缓存命中率: 78.50%
  操作计数:
    mrs_found: 15
    changes_extracted: 45
    fingerprints_generated: 128
  性能计时:
    validate_branch: 平均 2.345s (最大 3.120s, 总计 1 次)
    extract_changes: 平均 0.234s (最大 0.456s, 总计 15 次)
```

## 🚨 常见问题

### Q: 验证速度很慢怎么办？

**解决方案**：
1. 减少搜索天数：`--days 7`
2. 增加并行数：`--workers 8`
3. 启用缓存：在配置文件中设置文件缓存

### Q: 某些 MR 总是匹配失败？

**可能原因**：
1. MR 包含的都是文档或配置文件
2. 代码变更太小（少于5行）
3. 忽略模式过于宽泛

**解决方案**：
1. 检查 `fingerprint.ignore_patterns` 配置
2. 降低相似度阈值
3. 查看详细的匹配日志

### Q: GitLab API 访问失败？

**检查清单**：
1. Token 是否有效且有正确权限
2. 网络是否能访问 GitLab 服务器
3. Project ID 是否正确

## 📚 下一步

掌握基础用法后，建议了解：

1. [配置指南](configuration.md) - 详细的配置选项说明
2. [高级用法](advanced_usage.md) - 高级功能和最佳实践
3. [API 参考](../developer_guide/api_reference.md) - 编程接口文档

## 🤝 需要帮助？

- 📖 [完整文档](../README.md)
- 🐛 [报告问题](https://github.com/example/core-reflow/issues)
- 💬 [社区讨论](https://github.com/example/core-reflow/discussions)

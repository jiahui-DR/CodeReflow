# 配置指南

本指南详细介绍 Core Reflow 的所有配置选项，帮助您根据需要定制系统行为。

## 📋 配置文件格式

Core Reflow 使用 JSON 格式的配置文件。支持两种配置模式：

1. **单仓库配置** - 验证单个 Git 仓库
2. **多仓库配置** - 同时验证多个仓库

## 🔧 单仓库配置

### 完整配置示例

```json
{
  "gitlab": {
    "url": "https://gitlab.example.com",
    "token": "glpat-xxxxxxxxxxxxxxxxxxxx",
    "project_id": "123",
    "timeout": 30,
    "retry_attempts": 3,
    "verify_ssl": true
  },
  "git": {
    "repo_path": "/path/to/your/repo",
    "target_branch": "dev_master",
    "search_days": 30,
    "shallow_clone": false,
    "fetch_tags": true
  },
  "fingerprint": {
    "ignore_patterns": [
      "*.md",
      "*.txt",
      "*.json",
      "tests/*",
      "docs/*",
      ".gitignore",
      "README*"
    ],
    "min_lines": 5,
    "similarity_threshold": 0.8,
    "hash_algorithm": "sha256"
  },
  "output": {
    "format": "console",
    "file": null,
    "include_details": true,
    "color": true
  },
  "performance": {
    "max_workers": 4,
    "chunk_size": 10,
    "enable_metrics": true,
    "timeout": 300
  },
  "cache": {
    "backend": "memory",
    "max_size": 1000,
    "default_ttl": 3600,
    "cache_dir": ".cache",
    "cleanup_interval": 7200
  },
  "logging": {
    "level": "INFO",
    "format": "structured",
    "file": "logs/core_reflow.log",
    "max_size": "10MB",
    "backup_count": 5,
    "console_output": true
  }
}
```

### 配置项详细说明

#### 🌐 GitLab 配置 (`gitlab`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `url` | string | ✅ | - | GitLab 服务器 URL |
| `token` | string | ✅ | - | GitLab 访问令牌 |
| `project_id` | string | ✅ | - | 项目 ID 或路径 |
| `timeout` | integer | ❌ | 30 | API 请求超时时间（秒） |
| `retry_attempts` | integer | ❌ | 3 | API 请求重试次数 |
| `verify_ssl` | boolean | ❌ | true | 是否验证 SSL 证书 |

**Token 权限要求**：
- `api` - 访问 API
- `read_repository` - 读取仓库内容
- `read_user` - 读取用户信息

**获取 Project ID**：
```bash
# 方法1: 从项目页面 URL 获取
https://gitlab.example.com/group/project → project_id = "group/project"

# 方法2: 使用数字 ID
项目设置 → 通用 → 项目 ID → 123
```

#### 📁 Git 配置 (`git`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `repo_path` | string | ✅ | "." | Git 仓库本地路径 |
| `target_branch` | string | ✅ | "dev_master" | 目标主线分支 |
| `search_days` | integer | ❌ | 30 | 搜索时间范围（天） |
| `shallow_clone` | boolean | ❌ | false | 是否使用浅克隆 |
| `fetch_tags` | boolean | ❌ | true | 是否获取标签 |

**路径说明**：
- 绝对路径：`/home/user/projects/myapp`
- 相对路径：`./myapp`（相对于运行目录）
- 当前目录：`.`

#### 🔍 指纹配置 (`fingerprint`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ignore_patterns` | array | ❌ | [] | 忽略文件的通配符模式 |
| `min_lines` | integer | ❌ | 5 | 最小变更行数阈值 |
| `similarity_threshold` | float | ❌ | 0.8 | 相似度匹配阈值 |
| `hash_algorithm` | string | ❌ | "sha256" | 哈希算法 |

**忽略模式示例**：
```json
{
  "ignore_patterns": [
    "*.md",           // 所有 Markdown 文件
    "*.txt",          // 所有文本文件
    "tests/**",       // tests 目录下所有文件
    "docs/**",        // docs 目录下所有文件
    "**/migrations/**", // 任何位置的 migrations 目录
    ".gitignore",     // 特定文件名
    "package*.json"   // package.json, package-lock.json 等
  ]
}
```

#### 📤 输出配置 (`output`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `format` | string | ❌ | "console" | 输出格式：console/json/markdown |
| `file` | string | ❌ | null | 输出文件路径 |
| `include_details` | boolean | ❌ | true | 是否包含详细信息 |
| `color` | boolean | ❌ | true | 是否使用彩色输出 |

**输出格式对比**：

```bash
# 控制台输出（默认）
✅ MR #123: Add user auth - 已找到匹配 (98.5% 相似度)

# JSON 输出
{"mr_id": 123, "matched": true, "confidence": 0.985}

# Markdown 输出
| MR | 标题 | 状态 | 相似度 |
|----|------|------|--------|
| #123 | Add user auth | ✅ 匹配 | 98.5% |
```

#### ⚡ 性能配置 (`performance`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `max_workers` | integer | ❌ | 4 | 最大并行工作线程数 |
| `chunk_size` | integer | ❌ | 10 | 批处理块大小 |
| `enable_metrics` | boolean | ❌ | true | 是否启用性能指标 |
| `timeout` | integer | ❌ | 300 | 整体操作超时时间（秒） |

**性能调优建议**：
```json
{
  "performance": {
    // CPU 密集型：worker 数 = CPU 核心数
    "max_workers": 8,
    
    // 小仓库：较小的块大小
    "chunk_size": 5,
    
    // 大仓库：较大的块大小  
    "chunk_size": 20,
    
    // 网络慢：增加超时时间
    "timeout": 600
  }
}
```

#### 💾 缓存配置 (`cache`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `backend` | string | ❌ | "memory" | 缓存后端：memory/file |
| `max_size` | integer | ❌ | 1000 | 最大缓存条目数 |
| `default_ttl` | integer | ❌ | 3600 | 默认缓存生存时间（秒） |
| `cache_dir` | string | ❌ | ".cache" | 文件缓存目录 |
| `cleanup_interval` | integer | ❌ | 7200 | 清理间隔（秒） |

**缓存策略对比**：

```json
{
  // 内存缓存：速度快，重启丢失
  "cache": {
    "backend": "memory",
    "max_size": 1000,
    "default_ttl": 3600
  }
}
```

```json
{
  // 文件缓存：持久化，速度稍慢
  "cache": {
    "backend": "file", 
    "cache_dir": "/tmp/core_reflow_cache",
    "default_ttl": 86400  // 24小时
  }
}
```

#### 📝 日志配置 (`logging`)

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `level` | string | ❌ | "INFO" | 日志级别：DEBUG/INFO/WARNING/ERROR |
| `format` | string | ❌ | "structured" | 日志格式：structured/simple |
| `file` | string | ❌ | null | 日志文件路径 |
| `max_size` | string | ❌ | "10MB" | 日志文件最大大小 |
| `backup_count` | integer | ❌ | 5 | 备份文件数量 |
| `console_output` | boolean | ❌ | true | 是否输出到控制台 |

## 🏢 多仓库配置

### 配置文件示例

```json
{
  "repositories": [
    {
      "name": "Backend API",
      "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "glpat-backend-token",
        "project_id": "group/backend"
      },
      "git": {
        "repo_path": "/projects/backend",
        "target_branch": "dev_master"
      },
      "delivery_branches": [
        "delivery/v1.0.0",
        "delivery/v1.1.0"
      ]
    },
    {
      "name": "Frontend App", 
      "gitlab": {
        "url": "https://gitlab.example.com",
        "token": "glpat-frontend-token",
        "project_id": "group/frontend"
      },
      "git": {
        "repo_path": "/projects/frontend",
        "target_branch": "main"
      },
      "delivery_branches": [
        "delivery/v2.0.0"
      ]
    }
  ],
  "global_settings": {
    "search_days": 30,
    "max_workers": 8,
    "output_format": "json",
    "cache": {
      "backend": "file",
      "cache_dir": "/tmp/multi_repo_cache"
    },
    "logging": {
      "level": "INFO",
      "file": "logs/multi_repo.log"
    }
  }
}
```

### 使用多仓库配置

```bash
# 验证所有仓库的交付分支
core-reflow-cli --multi-repo delivery_config.json

# 验证特定仓库
core-reflow-cli --multi-repo delivery_config.json --repository "Backend API"
```

## 🌍 环境变量

支持使用环境变量覆盖配置：

```bash
# GitLab 配置
export GITLAB_URL="https://gitlab.company.com"
export GITLAB_TOKEN="glpat-your-token"
export GITLAB_PROJECT_ID="123"

# Git 配置
export GIT_REPO_PATH="/path/to/repo"
export GIT_TARGET_BRANCH="main"
export GIT_SEARCH_DAYS="60"

# 性能配置
export CORE_REFLOW_MAX_WORKERS="8"
export CORE_REFLOW_CACHE_BACKEND="file"

# 日志配置
export CORE_REFLOW_LOG_LEVEL="DEBUG"
export CORE_REFLOW_LOG_FILE="logs/debug.log"
```

**优先级顺序**：
1. 命令行参数（最高）
2. 环境变量
3. 配置文件
4. 默认值（最低）

## 🛠️ 配置验证

### 验证配置文件

```bash
# 验证配置语法
python -c "
import json
with open('config.json') as f:
    config = json.load(f)
print('✅ 配置文件格式正确')
"

# 使用工具验证
core-reflow --config config.json --validate-config
```

### 常见配置错误

#### 1. JSON 格式错误

```json
❌ 错误：
{
  "gitlab": {
    "url": "https://gitlab.com",
    "token": "abc123",  // 注释不允许
  }
}

✅ 正确：
{
  "gitlab": {
    "url": "https://gitlab.com", 
    "token": "abc123"
  }
}
```

#### 2. 路径错误

```json
❌ 错误：
{
  "git": {
    "repo_path": "~/projects/myapp"  // ~ 不会展开
  }
}

✅ 正确：
{
  "git": {
    "repo_path": "/home/user/projects/myapp"
  }
}
```

#### 3. 类型错误

```json
❌ 错误：
{
  "performance": {
    "max_workers": "4"  // 应该是数字
  }
}

✅ 正确：
{
  "performance": {
    "max_workers": 4
  }
}
```

## 🎛️ 高级配置

### 条件配置

根据环境使用不同配置：

```bash
# 开发环境
export ENV=development
core-reflow --config config-dev.json

# 生产环境  
export ENV=production
core-reflow --config config-prod.json
```

### 配置模板

创建配置模板文件：

```json
{
  "gitlab": {
    "url": "${GITLAB_URL}",
    "token": "${GITLAB_TOKEN}",
    "project_id": "${PROJECT_ID}"
  },
  "git": {
    "repo_path": "${REPO_PATH}",
    "target_branch": "${TARGET_BRANCH:-dev_master}"
  }
}
```

使用模板：
```bash
envsubst < config.template.json > config.json
```

### 动态配置

编程方式修改配置：

```python
from core_reflow.utils.config import ConfigManager

# 加载配置
config = ConfigManager('config.json')

# 动态修改
config.set('performance.max_workers', 8)
config.set('cache.backend', 'file')

# 保存配置
config.save('config-modified.json')
```

## 📋 配置最佳实践

### 1. 安全性

```json
{
  // ✅ 使用环境变量存储敏感信息
  "gitlab": {
    "token": "${GITLAB_TOKEN}"
  }
}
```

```bash
# 设置权限
chmod 600 config.json
```

### 2. 性能优化

```json
{
  // 根据机器配置调整
  "performance": {
    "max_workers": 4,  // CPU 核心数
    "chunk_size": 10   // 根据 MR 数量调整
  },
  
  // 启用缓存
  "cache": {
    "backend": "file",
    "default_ttl": 86400  // 24 小时
  }
}
```

### 3. 监控和调试

```json
{
  "logging": {
    "level": "INFO",           // 生产环境
    "level": "DEBUG",          // 调试时
    "file": "logs/app.log",
    "console_output": true
  },
  
  "performance": {
    "enable_metrics": true     // 启用性能监控
  }
}
```

### 4. 团队协作

```bash
# 提供配置示例
cp config.json config.example.json

# 忽略个人配置
echo "config.local.json" >> .gitignore

# 使用个人配置覆盖
core-reflow --config config.local.json
```

## 🔍 故障排除

### 检查配置加载

```bash
# 启用调试模式查看配置加载过程
core-reflow --config config.json --debug
```

### 配置测试

```python
# 测试 GitLab 连接
from core_reflow.gitlab_api.mr_processor import MRProcessor

processor = MRProcessor(
    token="your-token",
    project_id="123", 
    gitlab_url="https://gitlab.com"
)

# 测试连接
try:
    project = processor._gitlab.projects.get("123")
    print(f"✅ 连接成功: {project.name}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

### 常见问题解决

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Token 认证失败 | Token 过期或权限不足 | 重新生成 Token，确保有正确权限 |
| 仓库访问失败 | 路径错误或权限问题 | 检查路径是否存在，确保有读取权限 |
| 性能问题 | 配置不当 | 调整 workers 数量和缓存设置 |
| 缓存问题 | 缓存目录权限 | 检查缓存目录是否可写 |

## 📚 相关文档

- [快速开始](quick_start.md) - 基础使用方法
- [高级用法](advanced_usage.md) - 高级功能和技巧
- [API 参考](../developer_guide/api_reference.md) - 编程接口

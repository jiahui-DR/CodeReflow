# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

这是一个**代码变更指纹验证系统**，用于验证 GitLab 合并请求（MR）是否已合并到主线分支。该系统使用代码指纹技术准确识别代码变更的回流状态，支持直接合并、Cherry-pick 等多种合并场景。

## 核心架构

系统采用模块化架构，职责分离明确：

- **主入口**: `core_reflow/main.py` - CLI 接口和主要协调器
- **配置管理**: `core_reflow/utils/config.py` - 基于 JSON 的配置管理
- **GitLab 集成**: `core_reflow/gitlab/mr_processor.py` - 处理 GitLab API 交互
- **Git 操作**:
  - `core_reflow/git/extractor.py` - 从 MR 中提取代码变更
  - `core_reflow/git/searcher.py` - 在主线分支中搜索变更
- **指纹生成**: `core_reflow/fingerprint/generator.py` - 为代码变更创建唯一指纹
- **核心逻辑**:
  - `core_reflow/core/validator.py` - 验证匹配结果
  - `core_reflow/core/outputer.py` - 处理结果格式化和输出

## 开发命令

### 测试
```bash
# 运行基础功能测试
python3 test_basic.py

# 运行所有单元测试
python3 run_tests.py

# 运行特定测试
python3 run_tests.py tests.test_module.test_function
```

### 运行系统
```bash
# 运行完整演示了解系统功能
python3 demo_usage.py

# 验证分支中的所有 MR
python3 core_reflow/main.py --branch your-feature-branch --config config.json

# 验证特定 MR
python3 core_reflow/main.py --mr-id 123 --config config.json

# 示例用法
python3 examples/main_example.py --branch feature/your-branch --config config.json

# 高级用法：并行处理和性能监控
python3 core_reflow/main.py --branch feature/big-feature --workers 8 --metrics

# 清空缓存并搜索90天内的提交
python3 core_reflow/main.py --mr-id 456 --cache-clear --days 90
```

### 依赖项
```bash
# 安装必需的包
pip install -r requirements.txt
```

主要依赖：GitPython>=3.1.0, python-gitlab>=3.0.0, pytest>=6.2.0

### 代码质量
```bash
# 格式化代码
black .

# 代码检查
flake8 .

# 类型检查
mypy core_reflow/
```

## 配置

系统使用 JSON 配置文件。关键设置：

- **GitLab 设置**: `gitlab.url`, `gitlab.token`, `gitlab.project_id`
- **Git 设置**: `git.repo_path`, `git.target_branch` (默认: 'dev_master'), `git.search_days`
- **指纹设置**: `fingerprint.ignore_patterns` 用于过滤无关变更
- **缓存设置**: `cache.backend`, `cache.max_size`, `cache.default_ttl`
- **性能设置**: `performance.max_workers`, `performance.batch_size`
- **日志设置**: `logging.level`, `logging.file`, `logging.max_file_size`
- **输出设置**: `output.format` (console/json/markdown)

配置模板请参见 `examples/config.example.json`。

## 关键技术细节

### 代码流程
1. MR 处理器从 GitLab API 获取 MR 数据
2. 变更提取器处理 MR 差异并提取代码变更
3. 指纹生成器为每个变更创建唯一标识符
4. 主线分支搜索器在目标分支中查找匹配的变更
5. 匹配验证器确定变更是否已合并
6. 结果输出器格式化并显示结果

### 指纹算法
- 创建 16 位十六进制指纹
- 过滤掉注释、导入语句和仅空白行的变更
- 支持多种编程语言和文件类型
- 使用正则表达式模式忽略无关代码行

### 搜索策略
- 在指定时间范围内搜索（默认：30 天）
- 支持多种合并路径（直接合并、cherry-pick 等）
- 使用模糊匹配来处理微小变更
- 并行处理优化性能

### 缓存系统
- 内存和文件双重缓存后端
- 可配置的 TTL 和缓存大小
- 减少重复计算提升性能

### 性能特性
- 多线程并行处理 MR
- 可配置的工作线程数和批次大小
- 内置指标收集和监控
- 结构化日志和日志轮转

## 错误处理

系统包含完善的错误处理机制：
- 自定义异常层次结构（`CoreReflowError`, `ConfigurationError`, `GitLabAPIError` 等）
- 可配置级别的结构化日志
- 部分故障时的优雅降级
- 详细的错误消息和建议

## 文件结构说明

- 主要实现在 `core_reflow/` 目录
- 示例和配置模板在 `examples/` 目录
- 单元测试在 `tests/` 目录
- 文档包括中文和英文
- 设计文档详细描述了技术方案
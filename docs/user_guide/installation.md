# 安装指南

## 🚀 快速安装

### 方法一：从源码安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/example/core-reflow.git
cd core-reflow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装包
pip install -e .
```

### 方法二：使用pip安装

```bash
# 从PyPI安装（如果已发布）
pip install core-reflow
```

### 方法三：开发安装

```bash
# 1. 克隆仓库
git clone https://github.com/example/core-reflow.git
cd core-reflow

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者 venv\Scripts\activate  # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
pip install -e .[dev]
```

## 📋 系统要求

### 必需要求

- **Python**: 3.7 或更高版本
- **Git**: 用于仓库操作
- **网络连接**: 访问GitLab API

### 推荐配置

- **操作系统**: Linux, macOS, Windows
- **内存**: 至少 2GB RAM
- **存储**: 至少 1GB 可用空间
- **CPU**: 多核处理器（用于并行处理）

## 🔧 依赖说明

### 核心依赖

```
requests>=2.25.0          # HTTP请求
gitpython>=3.1.0          # Git操作
python-gitlab>=3.0.0      # GitLab API客户端
click>=8.0.0              # 命令行界面
pydantic>=1.8.0           # 数据验证
```

### 可选依赖

```
# 开发工具
pytest>=7.0.0             # 测试框架
pytest-cov>=4.0.0         # 测试覆盖率
black>=22.0.0             # 代码格式化
flake8>=5.0.0             # 代码检查
mypy>=0.950               # 类型检查

# 性能工具
psutil>=5.8.0             # 系统监控
memory-profiler>=0.60.0   # 内存分析
```

## ✅ 安装验证

### 1. 验证安装

```bash
# 检查命令是否可用
core-reflow --version
core-reflow-cli --version

# 查看帮助信息
core-reflow --help
core-reflow-cli --help
```

### 2. 运行示例

```bash
# 进入示例目录
cd examples/

# 运行基础示例
python basic_usage.py

# 运行交付分支演示
python delivery_branch_demo.py
```

### 3. 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/unit/
python -m pytest tests/integration/

# 生成覆盖率报告
python -m pytest tests/ --cov=core_reflow --cov-report=html
```

## 🛠️ 配置环境

### 1. 创建配置文件

```bash
# 使用交互式向导创建配置
core-reflow-cli --interactive

# 或者查看配置示例
core-reflow-cli --config-example single
core-reflow-cli --config-example delivery
```

### 2. 设置GitLab访问

```bash
# 设置环境变量
export GITLAB_TOKEN="your-gitlab-token"
export GITLAB_URL="https://gitlab.example.com"
```

### 3. 配置Git仓库

```bash
# 确保有访问权限
git clone https://gitlab.example.com/group/project.git
cd project

# 检查分支
git branch -a
```

## 🐛 常见问题

### Q1: 安装时出现权限错误

**问题**：`Permission denied` 或 `Access denied`

**解决方案**：
```bash
# 使用用户安装
pip install --user -r requirements.txt

# 或者使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Q2: Git操作失败

**问题**：`GitCommandError` 或无法访问仓库

**解决方案**：
1. 检查Git配置：
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. 配置SSH密钥：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your.email@example.com"
   ssh-add ~/.ssh/id_rsa
   ```

3. 检查仓库权限：
   ```bash
   git ls-remote https://gitlab.example.com/group/project.git
   ```

### Q3: GitLab API认证失败

**问题**：`401 Unauthorized` 或 `403 Forbidden`

**解决方案**：
1. 检查Token权限：
   - 访问GitLab → 用户设置 → Access Tokens
   - 确保Token有 `api`, `read_repository` 权限

2. 验证Token：
   ```bash
   curl -H "PRIVATE-TOKEN: your-token" \
        "https://gitlab.example.com/api/v4/user"
   ```

### Q4: 性能问题

**问题**：处理速度慢或内存占用高

**解决方案**：
1. 调整并行度：
   ```bash
   core-reflow --workers 2  # 减少并行数
   ```

2. 启用缓存：
   ```json
   {
     "cache": {
       "backend": "file",
       "cache_dir": ".cache"
     }
   }
   ```

3. 限制搜索范围：
   ```bash
   core-reflow --days 7  # 只搜索最近7天
   ```

## 📚 下一步

安装完成后，建议阅读：

1. [快速开始指南](quick_start.md) - 学习基本使用方法
2. [配置指南](configuration.md) - 了解详细配置选项
3. [高级用法](advanced_usage.md) - 探索高级功能

## 🤝 获取帮助

如果遇到问题：

1. **查看文档**: [在线文档](https://core-reflow.readthedocs.io/)
2. **提交Issue**: [GitHub Issues](https://github.com/example/core-reflow/issues)
3. **讨论交流**: [讨论区](https://github.com/example/core-reflow/discussions)
4. **邮件联系**: core-reflow@example.com

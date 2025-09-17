#!/bin/bash

# Core Reflow 开发环境设置脚本
# 该脚本帮助开发者快速设置开发环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python 版本
check_python_version() {
    log_info "检查 Python 版本..."
    
    if ! command_exists python3; then
        log_error "Python 3 未安装，请先安装 Python 3.7 或更高版本"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.7"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        log_error "Python 版本 $python_version 不满足要求，需要 $required_version 或更高版本"
        exit 1
    fi
    
    log_success "Python 版本检查通过: $python_version"
}

# 检查 Git
check_git() {
    log_info "检查 Git..."
    
    if ! command_exists git; then
        log_error "Git 未安装，请先安装 Git"
        exit 1
    fi
    
    git_version=$(git --version | cut -d' ' -f3)
    log_success "Git 版本: $git_version"
}

# 创建虚拟环境
create_virtual_env() {
    log_info "创建 Python 虚拟环境..."
    
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在，是否重新创建? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    python3 -m venv venv
    log_success "虚拟环境创建完成"
}

# 激活虚拟环境
activate_virtual_env() {
    log_info "激活虚拟环境..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_success "虚拟环境已激活"
    else
        log_error "虚拟环境激活脚本不存在"
        exit 1
    fi
}

# 升级 pip
upgrade_pip() {
    log_info "升级 pip..."
    python -m pip install --upgrade pip
    log_success "pip 升级完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "项目依赖安装完成"
    else
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 安装开发依赖
    log_info "安装开发依赖..."
    pip install pytest pytest-cov pytest-mock black flake8 mypy pre-commit
    log_success "开发依赖安装完成"
}

# 安装项目为可编辑模式
install_project() {
    log_info "安装项目为可编辑模式..."
    pip install -e .
    log_success "项目安装完成"
}

# 设置 pre-commit 钩子
setup_pre_commit() {
    log_info "设置 pre-commit 钩子..."
    
    if command_exists pre-commit; then
        if [ -f ".pre-commit-config.yaml" ]; then
            pre-commit install
            log_success "pre-commit 钩子设置完成"
        else
            log_warning ".pre-commit-config.yaml 不存在，创建默认配置..."
            create_pre_commit_config
            pre-commit install
            log_success "pre-commit 钩子设置完成"
        fi
    else
        log_warning "pre-commit 未安装，跳过钩子设置"
    fi
}

# 创建 pre-commit 配置
create_pre_commit_config() {
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
EOF
}

# 创建开发配置文件
create_dev_config() {
    log_info "创建开发配置文件..."
    
    if [ ! -f "config/config.dev.json" ]; then
        mkdir -p config
        cat > config/config.dev.json << 'EOF'
{
  "gitlab": {
    "url": "https://gitlab.example.com",
    "token": "your-development-token",
    "project_id": "your-project-id"
  },
  "git": {
    "repo_path": ".",
    "target_branch": "dev_master",
    "search_days": 7
  },
  "fingerprint": {
    "ignore_patterns": [
      "*.md",
      "*.txt",
      "tests/*",
      "docs/*"
    ]
  },
  "output": {
    "format": "console"
  },
  "performance": {
    "max_workers": 2,
    "enable_metrics": true
  },
  "cache": {
    "backend": "memory",
    "max_size": 100
  },
  "logging": {
    "level": "DEBUG",
    "format": "structured",
    "file": "logs/dev.log",
    "console_output": true
  }
}
EOF
        log_success "开发配置文件创建完成: config/config.dev.json"
    else
        log_info "开发配置文件已存在"
    fi
}

# 创建目录结构
create_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "logs"
        ".cache"
        "tests/fixtures"
        "docs/images"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    # 创建 .gitkeep 文件
    touch logs/.gitkeep
    touch .cache/.gitkeep
    
    log_success "目录结构创建完成"
}

# 运行测试验证
run_tests() {
    log_info "运行测试验证安装..."
    
    if python -m pytest tests/ -v; then
        log_success "所有测试通过"
    else
        log_warning "部分测试失败，但不影响开发环境设置"
    fi
}

# 生成开发指南
generate_dev_guide() {
    log_info "生成开发指南..."
    
    cat > DEV_SETUP.md << 'EOF'
# 开发环境设置完成

## 🎉 环境状态

✅ Python 虚拟环境已创建并激活
✅ 项目依赖已安装
✅ 开发工具已配置
✅ pre-commit 钩子已设置
✅ 开发配置文件已创建

## 🚀 开始开发

### 激活虚拟环境
```bash
source venv/bin/activate
```

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/unit/

# 生成覆盖率报告
python -m pytest --cov=core_reflow --cov-report=html
```

### 代码格式化
```bash
# 自动格式化代码
black core_reflow/ tests/

# 检查代码风格
flake8 core_reflow/ tests/

# 类型检查
mypy core_reflow/
```

### 运行示例
```bash
# 基础示例
python examples/basic_usage.py

# 交付分支演示
python examples/delivery_branch_demo.py
```

### 调试模式
```bash
# 启用调试日志
export CORE_REFLOW_LOG_LEVEL=DEBUG

# 使用开发配置
core-reflow --config config/config.dev.json --branch test-branch
```

## 📁 重要文件

- `config/config.dev.json` - 开发配置文件
- `logs/dev.log` - 开发日志文件
- `.pre-commit-config.yaml` - 代码检查配置
- `requirements.txt` - 项目依赖

## 🛠️ 开发工具

- `black` - 代码格式化
- `flake8` - 代码风格检查
- `mypy` - 类型检查
- `pytest` - 测试框架
- `pre-commit` - Git 钩子

## 📝 贡献指南

1. 创建功能分支
2. 编写代码和测试
3. 运行代码检查: `pre-commit run --all-files`
4. 提交代码
5. 创建 Pull Request

祝开发愉快！🎈
EOF

    log_success "开发指南已生成: DEV_SETUP.md"
}

# 显示完成信息
show_completion() {
    log_success "🎉 开发环境设置完成！"
    echo
    echo "请运行以下命令激活虚拟环境:"
    echo "  source venv/bin/activate"
    echo
    echo "然后可以开始开发:"
    echo "  python examples/basic_usage.py"
    echo "  python -m pytest tests/"
    echo
    echo "查看完整的开发指南:"
    echo "  cat DEV_SETUP.md"
    echo
}

# 主函数
main() {
    echo "🚀 开始设置 Core Reflow 开发环境..."
    echo
    
    # 检查先决条件
    check_python_version
    check_git
    
    # 设置虚拟环境
    create_virtual_env
    activate_virtual_env
    upgrade_pip
    
    # 安装依赖
    install_dependencies
    install_project
    
    # 设置开发工具
    setup_pre_commit
    
    # 创建配置和目录
    create_dev_config
    create_directories
    
    # 验证安装
    run_tests
    
    # 生成文档
    generate_dev_guide
    
    # 显示完成信息
    show_completion
}

# 脚本参数处理
case "${1:-}" in
    --help|-h)
        echo "Core Reflow 开发环境设置脚本"
        echo
        echo "用法: $0 [选项]"
        echo
        echo "选项:"
        echo "  --help, -h     显示此帮助信息"
        echo "  --skip-tests   跳过测试验证"
        echo "  --minimal      最小化安装（跳过可选组件）"
        echo
        exit 0
        ;;
    --skip-tests)
        SKIP_TESTS=1
        ;;
    --minimal)
        MINIMAL_INSTALL=1
        ;;
esac

# 运行主函数
main

#!/bin/bash

# Core Reflow 代码格式化脚本
# 使用 black, flake8, isort 等工具进行代码格式化和检查

set -e

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

# 检查工具是否安装
check_tool() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 未安装，请先安装: pip install $1"
        return 1
    fi
    return 0
}

# 格式化 Python 代码
format_python() {
    log_info "使用 black 格式化 Python 代码..."
    
    if check_tool black; then
        black core_reflow/ tests/ examples/ scripts/ --line-length 88 --target-version py37
        log_success "Python 代码格式化完成"
    else
        return 1
    fi
}

# 排序导入语句
sort_imports() {
    log_info "使用 isort 排序导入语句..."
    
    if check_tool isort; then
        isort core_reflow/ tests/ examples/ --profile black --line-length 88
        log_success "导入语句排序完成"
    else
        log_warning "isort 未安装，跳过导入排序。安装命令: pip install isort"
    fi
}

# 代码风格检查
check_style() {
    log_info "使用 flake8 检查代码风格..."
    
    if check_tool flake8; then
        if flake8 core_reflow/ tests/ examples/ \
            --max-line-length=88 \
            --extend-ignore=E203,W503,E501 \
            --exclude=venv,__pycache__,.git,build,dist; then
            log_success "代码风格检查通过"
            return 0
        else
            log_error "代码风格检查失败"
            return 1
        fi
    else
        return 1
    fi
}

# 类型检查
check_types() {
    log_info "使用 mypy 进行类型检查..."
    
    if check_tool mypy; then
        if mypy core_reflow/ \
            --ignore-missing-imports \
            --no-strict-optional \
            --allow-untyped-decorators; then
            log_success "类型检查通过"
            return 0
        else
            log_warning "类型检查发现问题，建议修复"
            return 1
        fi
    else
        log_warning "mypy 未安装，跳过类型检查。安装命令: pip install mypy"
        return 0
    fi
}

# 安全检查
security_check() {
    log_info "使用 bandit 进行安全检查..."
    
    if check_tool bandit; then
        if bandit -r core_reflow/ -f json -o security-report.json; then
            log_success "安全检查通过"
            return 0
        else
            log_warning "安全检查发现问题，请查看 security-report.json"
            return 1
        fi
    else
        log_warning "bandit 未安装，跳过安全检查。安装命令: pip install bandit"
        return 0
    fi
}

# 复杂度检查
complexity_check() {
    log_info "使用 radon 检查代码复杂度..."
    
    if check_tool radon; then
        echo "=== 圈复杂度报告 ==="
        radon cc core_reflow/ -a -s
        
        echo -e "\n=== 可维护性指数 ==="
        radon mi core_reflow/ -s
        
        log_success "复杂度检查完成"
    else
        log_warning "radon 未安装，跳过复杂度检查。安装命令: pip install radon"
    fi
}

# 生成代码质量报告
generate_quality_report() {
    log_info "生成代码质量报告..."
    
    report_file="code_quality_report.md"
    
    cat > "$report_file" << EOF
# 代码质量报告

生成时间: $(date '+%Y-%m-%d %H:%M:%S')

## 📊 统计信息

EOF
    
    # 代码行数统计
    if command -v cloc >/dev/null 2>&1; then
        echo "### 代码行数统计" >> "$report_file"
        echo '```' >> "$report_file"
        cloc core_reflow/ --exclude-dir=__pycache__ >> "$report_file"
        echo '```' >> "$report_file"
        echo >> "$report_file"
    fi
    
    # 测试覆盖率
    if command -v pytest >/dev/null 2>&1; then
        echo "### 测试覆盖率" >> "$report_file"
        echo '```' >> "$report_file"
        pytest --cov=core_reflow --cov-report=term-missing tests/ >> "$report_file" 2>&1 || true
        echo '```' >> "$report_file"
        echo >> "$report_file"
    fi
    
    # 代码复杂度
    if command -v radon >/dev/null 2>&1; then
        echo "### 圈复杂度" >> "$report_file"
        echo '```' >> "$report_file"
        radon cc core_reflow/ -a >> "$report_file"
        echo '```' >> "$report_file"
        echo >> "$report_file"
        
        echo "### 可维护性指数" >> "$report_file"
        echo '```' >> "$report_file"
        radon mi core_reflow/ >> "$report_file"
        echo '```' >> "$report_file"
        echo >> "$report_file"
    fi
    
    log_success "代码质量报告已生成: $report_file"
}

# 修复常见问题
auto_fix() {
    log_info "自动修复常见代码问题..."
    
    # 移除尾随空格
    if command -v sed >/dev/null 2>&1; then
        find core_reflow/ tests/ examples/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \;
        log_info "移除尾随空格"
    fi
    
    # 确保文件以换行符结尾
    if command -v find >/dev/null 2>&1; then
        find core_reflow/ tests/ examples/ -name "*.py" -exec sh -c 'tail -c1 "$0" | read -r _ || echo >> "$0"' {} \;
        log_info "确保文件以换行符结尾"
    fi
    
    log_success "自动修复完成"
}

# 安装所需工具
install_tools() {
    log_info "安装代码格式化工具..."
    
    tools=(
        "black"
        "flake8"
        "isort"
        "mypy"
        "bandit"
        "radon"
        "pre-commit"
    )
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_info "安装 $tool..."
            pip install "$tool"
        else
            log_info "$tool 已安装"
        fi
    done
    
    log_success "所有工具安装完成"
}

# 显示使用帮助
show_help() {
    cat << 'EOF'
Core Reflow 代码格式化脚本

用法: ./scripts/format_code.sh [选项]

选项:
  --help, -h           显示此帮助信息
  --install-tools      安装所需的格式化工具
  --format-only        仅格式化代码，不进行检查
  --check-only         仅检查代码，不格式化
  --fix                自动修复常见问题
  --report             生成代码质量报告
  --all                执行所有操作（默认）

示例:
  ./scripts/format_code.sh                    # 执行所有操作
  ./scripts/format_code.sh --format-only     # 仅格式化
  ./scripts/format_code.sh --check-only      # 仅检查
  ./scripts/format_code.sh --install-tools   # 安装工具
EOF
}

# 主函数
main() {
    local format_only=false
    local check_only=false
    local install_tools_only=false
    local auto_fix_only=false
    local report_only=false
    local exit_code=0
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --install-tools)
                install_tools_only=true
                shift
                ;;
            --format-only)
                format_only=true
                shift
                ;;
            --check-only)
                check_only=true
                shift
                ;;
            --fix)
                auto_fix_only=true
                shift
                ;;
            --report)
                report_only=true
                shift
                ;;
            --all)
                # 默认行为，所有操作
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "🛠️ Core Reflow 代码格式化和检查"
    echo "=================================="
    
    # 执行特定操作
    if [[ "$install_tools_only" == true ]]; then
        install_tools
        exit 0
    fi
    
    if [[ "$auto_fix_only" == true ]]; then
        auto_fix
        exit 0
    fi
    
    if [[ "$report_only" == true ]]; then
        generate_quality_report
        exit 0
    fi
    
    # 格式化操作
    if [[ "$check_only" != true ]]; then
        log_info "开始代码格式化..."
        
        if ! format_python; then
            exit_code=1
        fi
        
        if ! sort_imports; then
            exit_code=1
        fi
        
        auto_fix
    fi
    
    # 检查操作
    if [[ "$format_only" != true ]]; then
        log_info "开始代码检查..."
        
        if ! check_style; then
            exit_code=1
        fi
        
        if ! check_types; then
            exit_code=1
        fi
        
        if ! security_check; then
            exit_code=1
        fi
        
        complexity_check
    fi
    
    # 生成报告
    generate_quality_report
    
    # 结果汇总
    echo
    if [[ $exit_code -eq 0 ]]; then
        log_success "所有检查通过！代码质量良好 ✨"
    else
        log_warning "发现一些问题，请检查上述输出并修复"
    fi
    
    exit $exit_code
}

# 运行主函数
main "$@"

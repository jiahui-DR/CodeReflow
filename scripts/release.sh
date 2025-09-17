#!/bin/bash

# Core Reflow 发布脚本
# 自动化版本发布流程，包括版本检查、构建、测试和发布

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

# 配置
PROJECT_NAME="core-reflow"
PYTHON_MODULE="core_reflow"
MAIN_BRANCH="main"
DEVELOP_BRANCH="develop"

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查先决条件
check_prerequisites() {
    log_info "检查发布先决条件..."
    
    # 检查必要工具
    local tools=("git" "python3" "pip" "twine")
    for tool in "${tools[@]}"; do
        if ! command_exists "$tool"; then
            log_error "$tool 未安装"
            exit 1
        fi
    done
    
    # 检查 Git 状态
    if [ -n "$(git status --porcelain)" ]; then
        log_error "工作目录不干净，请先提交或暂存更改"
        exit 1
    fi
    
    # 检查当前分支
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$MAIN_BRANCH" ] && [ "$current_branch" != "$DEVELOP_BRANCH" ]; then
        log_warning "当前分支: $current_branch，建议在 $MAIN_BRANCH 或 $DEVELOP_BRANCH 分支发布"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "先决条件检查通过"
}

# 获取当前版本
get_current_version() {
    if [ -f "setup.py" ]; then
        python3 setup.py --version 2>/dev/null || echo "0.0.0"
    elif [ -f "pyproject.toml" ]; then
        python3 -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || echo "0.0.0"
    else
        echo "0.0.0"
    fi
}

# 验证版本格式
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "版本格式错误: $version (应为: x.y.z)"
        return 1
    fi
    return 0
}

# 更新版本号
update_version() {
    local new_version=$1
    
    log_info "更新版本号为: $new_version"
    
    # 更新 setup.py
    if [ -f "setup.py" ]; then
        sed -i "s/version=\"[^\"]*\"/version=\"$new_version\"/" setup.py
        log_info "更新 setup.py"
    fi
    
    # 更新 __init__.py
    if [ -f "$PYTHON_MODULE/__init__.py" ]; then
        if grep -q "__version__" "$PYTHON_MODULE/__init__.py"; then
            sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$new_version\"/" "$PYTHON_MODULE/__init__.py"
        else
            echo "__version__ = \"$new_version\"" >> "$PYTHON_MODULE/__init__.py"
        fi
        log_info "更新 $PYTHON_MODULE/__init__.py"
    fi
    
    # 更新 README.md 中的版本引用
    if [ -f "README.md" ]; then
        sed -i "s/version-[0-9]\+\.[0-9]\+\.[0-9]\+/version-$new_version/g" README.md
        log_info "更新 README.md"
    fi
    
    log_success "版本号更新完成"
}

# 运行完整测试套件
run_tests() {
    log_info "运行完整测试套件..."
    
    # 单元测试
    if ! python -m pytest tests/unit/ -v; then
        log_error "单元测试失败"
        return 1
    fi
    
    # 集成测试
    if ! python -m pytest tests/integration/ -v; then
        log_error "集成测试失败"
        return 1
    fi
    
    # 代码覆盖率检查
    if command_exists coverage; then
        if ! python -m pytest tests/ --cov="$PYTHON_MODULE" --cov-report=term-missing --cov-fail-under=80; then
            log_error "代码覆盖率不足 80%"
            return 1
        fi
    fi
    
    log_success "所有测试通过"
    return 0
}

# 代码质量检查
quality_check() {
    log_info "进行代码质量检查..."
    
    # 代码格式检查
    if command_exists black; then
        if ! black --check "$PYTHON_MODULE/" tests/; then
            log_error "代码格式检查失败，请运行 black"
            return 1
        fi
    fi
    
    # 代码风格检查
    if command_exists flake8; then
        if ! flake8 "$PYTHON_MODULE/" tests/ --max-line-length=88 --extend-ignore=E203,W503; then
            log_error "代码风格检查失败"
            return 1
        fi
    fi
    
    # 类型检查
    if command_exists mypy; then
        if ! mypy "$PYTHON_MODULE/" --ignore-missing-imports; then
            log_warning "类型检查发现问题，但不阻止发布"
        fi
    fi
    
    log_success "代码质量检查通过"
    return 0
}

# 构建分发包
build_package() {
    log_info "构建分发包..."
    
    # 清理旧的构建文件
    rm -rf build/ dist/ *.egg-info/
    
    # 构建源码分发和轮子
    python3 setup.py sdist bdist_wheel
    
    # 检查分发包
    if command_exists twine; then
        twine check dist/*
    fi
    
    log_success "分发包构建完成"
}

# 生成变更日志
generate_changelog() {
    local version=$1
    local changelog_file="CHANGELOG.md"
    
    log_info "生成变更日志..."
    
    # 获取上一个版本标签
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    # 如果没有变更日志文件，创建一个
    if [ ! -f "$changelog_file" ]; then
        cat > "$changelog_file" << 'EOF'
# 变更日志

所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

EOF
    fi
    
    # 生成当前版本的变更记录
    local temp_file=$(mktemp)
    cat > "$temp_file" << EOF

## [$version] - $(date +%Y-%m-%d)

### 新增
- 版本 $version 发布

### 变更
EOF
    
    # 如果有上一个标签，获取提交记录
    if [ -n "$last_tag" ]; then
        echo "- 详细变更请查看: https://github.com/example/$PROJECT_NAME/compare/$last_tag...v$version" >> "$temp_file"
        
        # 提取提交信息
        echo -e "\n### 提交记录" >> "$temp_file"
        git log --oneline "${last_tag}..HEAD" | sed 's/^/- /' >> "$temp_file"
    else
        echo "- 初始版本发布" >> "$temp_file"
    fi
    
    # 将新记录插入到变更日志开头
    sed -i "/^# 变更日志/r $temp_file" "$changelog_file"
    rm "$temp_file"
    
    log_success "变更日志已更新"
}

# 创建 Git 标签
create_git_tag() {
    local version=$1
    local tag_name="v$version"
    
    log_info "创建 Git 标签: $tag_name"
    
    # 提交版本更新
    git add -A
    git commit -m "chore: bump version to $version"
    
    # 创建标签
    git tag -a "$tag_name" -m "Release version $version"
    
    log_success "Git 标签已创建"
}

# 发布到 PyPI
publish_to_pypi() {
    local dry_run=$1
    
    if [ "$dry_run" = true ]; then
        log_info "执行 PyPI 发布预检（干运行）..."
        twine upload --repository testpypi dist/* --verbose
    else
        log_info "发布到 PyPI..."
        read -p "确认发布到 PyPI? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            twine upload dist/*
            log_success "已发布到 PyPI"
        else
            log_info "取消 PyPI 发布"
        fi
    fi
}

# 推送到远程仓库
push_to_remote() {
    log_info "推送到远程仓库..."
    
    read -p "推送标签和提交到远程仓库? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin HEAD
        git push origin --tags
        log_success "已推送到远程仓库"
    else
        log_info "跳过推送到远程仓库"
    fi
}

# 创建 GitHub Release
create_github_release() {
    local version=$1
    
    if command_exists gh; then
        log_info "创建 GitHub Release..."
        
        read -p "创建 GitHub Release? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 从变更日志提取发布说明
            local release_notes=$(awk "/## \[$version\]/,/## \[/{if(/## \[/ && !/## \[$version\]/) exit; print}" CHANGELOG.md | tail -n +2 | head -n -1)
            
            gh release create "v$version" dist/* \
                --title "Release v$version" \
                --notes "$release_notes"
            
            log_success "GitHub Release 已创建"
        fi
    else
        log_info "GitHub CLI 未安装，跳过创建 GitHub Release"
    fi
}

# 清理构建文件
cleanup() {
    log_info "清理构建文件..."
    rm -rf build/ *.egg-info/
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    cat << 'EOF'
Core Reflow 发布脚本

用法: ./scripts/release.sh [选项] <版本号>

参数:
  <版本号>    要发布的版本号 (格式: x.y.z)

选项:
  --help, -h        显示此帮助信息
  --dry-run         执行预检，不实际发布
  --skip-tests      跳过测试
  --skip-quality    跳过代码质量检查
  --skip-build      跳过构建（用于重新发布）
  --skip-pypi       跳过 PyPI 发布
  --skip-push       跳过推送到远程仓库

示例:
  ./scripts/release.sh 1.2.3              # 发布版本 1.2.3
  ./scripts/release.sh --dry-run 1.2.3    # 预检版本 1.2.3
  ./scripts/release.sh --skip-tests 1.2.3 # 跳过测试发布
EOF
}

# 主函数
main() {
    local version=""
    local dry_run=false
    local skip_tests=false
    local skip_quality=false
    local skip_build=false
    local skip_pypi=false
    local skip_push=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-quality)
                skip_quality=true
                shift
                ;;
            --skip-build)
                skip_build=true
                shift
                ;;
            --skip-pypi)
                skip_pypi=true
                shift
                ;;
            --skip-push)
                skip_push=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$version" ]; then
                    version=$1
                else
                    log_error "多余的参数: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # 检查版本号
    if [ -z "$version" ]; then
        current_version=$(get_current_version)
        log_info "当前版本: $current_version"
        echo "请指定要发布的版本号"
        show_help
        exit 1
    fi
    
    if ! validate_version "$version"; then
        exit 1
    fi
    
    # 显示发布信息
    echo "🚀 Core Reflow 发布流程"
    echo "======================="
    echo "版本: $version"
    echo "干运行: $dry_run"
    echo
    
    # 检查先决条件
    check_prerequisites
    
    # 更新版本号
    if [ "$dry_run" != true ]; then
        update_version "$version"
        generate_changelog "$version"
    fi
    
    # 质量检查
    if [ "$skip_quality" != true ]; then
        quality_check || exit 1
    fi
    
    # 运行测试
    if [ "$skip_tests" != true ]; then
        run_tests || exit 1
    fi
    
    # 构建包
    if [ "$skip_build" != true ]; then
        build_package
    fi
    
    if [ "$dry_run" = true ]; then
        log_success "预检完成！所有检查通过，可以进行正式发布"
        exit 0
    fi
    
    # 创建标签
    create_git_tag "$version"
    
    # 发布到 PyPI
    if [ "$skip_pypi" != true ]; then
        publish_to_pypi false
    fi
    
    # 推送到远程
    if [ "$skip_push" != true ]; then
        push_to_remote
    fi
    
    # 创建 GitHub Release
    create_github_release "$version"
    
    # 清理
    cleanup
    
    # 完成
    echo
    log_success "🎉 版本 $version 发布完成！"
    echo
    echo "后续步骤:"
    echo "1. 检查 PyPI 页面: https://pypi.org/project/$PROJECT_NAME/"
    echo "2. 检查 GitHub Release: https://github.com/example/$PROJECT_NAME/releases"
    echo "3. 更新文档站点（如有）"
    echo "4. 通知用户新版本发布"
}

# 捕获中断信号
trap 'log_error "发布过程被中断"; exit 130' INT

# 运行主函数
main "$@"

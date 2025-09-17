# 配置文件说明

本目录包含MR回流验证系统的各种配置文件模板和示例。

## 📋 **配置文件类型**

### 1. **单仓库配置 - config.example.json**
用于验证单个Git仓库的MR回流状态。

```bash
# 复制并编辑单仓库配置
cp config.example.json config.json
vim config.json  # 设置你的GitLab token和项目信息
```

### 2. **多仓库配置 - delivery_config.example.json**
用于同时验证多个Git仓库的交付分支MR。

```bash
# 复制并编辑多仓库配置
cp delivery_config.example.json delivery_config.json
vim delivery_config.json  # 配置多个仓库信息
```

## 🔧 **配置字段说明**

### **GitLab配置**
- `gitlab.url`: GitLab服务器地址
- `gitlab.token`: GitLab个人访问令牌（需要API权限）
- `gitlab.project_id`: GitLab项目ID（数字）

### **Git配置**
- `git.repo_path`: 本地Git仓库路径（绝对路径）
- `git.target_branch`: 主线分支名称（如dev_master、main）
- `git.search_days`: 搜索时间范围（天数）

### **交付分支配置**（多仓库模式）
- `git.delivery_branch`: 交付分支名称

### **性能配置**
- `performance.max_workers`: 并行处理线程数
- `performance.batch_size`: 批处理大小
- `performance.enable_metrics`: 是否启用性能指标

### **缓存配置**
- `cache.backend`: 缓存后端类型（memory/file）
- `cache.max_size`: 缓存最大大小
- `cache.default_ttl`: 缓存生存时间（秒）

## 🚀 **快速开始**

1. **配置GitLab访问**
   ```bash
   # 在GitLab中创建Personal Access Token
   # 权限：api, read_repository, read_user
   ```

2. **设置单仓库验证**
   ```bash
   cp config.example.json config.json
   # 编辑config.json，填入你的信息
   ```

3. **测试配置**
   ```bash
   # 验证配置是否正确
   python3 core_reflow/main.py --mr-id 123 --config config/config.json
   ```

## ⚠️ **注意事项**

- **安全性**: 请勿将包含真实token的配置文件提交到版本控制
- **路径**: 使用绝对路径来避免路径问题
- **权限**: 确保GitLab token有足够的权限访问项目
- **网络**: 确保可以访问GitLab服务器和Git仓库

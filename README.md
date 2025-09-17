# 代码变更指纹验证系统 v2.0

## 项目概述

一个**企业级**的GitLab MR（Merge Request）回流验证系统。通过先进的代码指纹技术，准确识别代码变更的回流状态，支持直接合并、Cherry-pick等多种合并场景。

### 🎯 v2.0 新特性

- ⚡ **并行处理** - 支持多线程并行处理MR，大幅提升验证速度
- 🧠 **智能缓存** - 内存和文件双重缓存，减少重复计算，提升性能
- 📊 **性能监控** - 完整的性能指标收集和监控系统
- 🛡️ **健壮性提升** - 完善的错误处理和输入验证机制
- 🧪 **测试覆盖** - 29个单元测试，保证代码质量
- 📝 **结构化日志** - 详细的日志记录，便于问题诊断
- 🔧 **高度可配置** - 支持缓存、性能、日志等多维度配置

## 📁 项目结构

```
core_reflow/
├── config/          # 📋 配置文件和模板
├── core_reflow/     # 🔧 核心代码包
├── docs/           # 📖 完整文档体系
├── examples/       # 📚 示例和演示
├── tests/          # 🧪 测试代码
├── scripts/        # 🛠️ 辅助脚本
└── logs/           # 📝 日志文件
```

## 快速开始

### 1. 运行演示
```bash
# 运行完整演示，了解系统功能
python3 examples/basic_usage.py
```

### 2. 安装依赖
```bash
# 安装必要的Python包
pip install -r requirements.txt
```

### 3. 配置系统
```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 编辑配置文件
vim config/config.json  # 设置GitLab token和项目信息
```

### 4. 运行测试
```bash
# 运行所有测试
python3 scripts/run_tests.py

# 运行示例演示
python3 examples/basic_usage.py
```

### 5. 开始使用

#### 基础使用
```bash
# 验证分支的所有MR
python3 core_reflow/main.py --branch your-feature-branch --config config/config.json

# 验证特定MR
python3 core_reflow/main.py --mr-id 123 --config config/config.json
```

#### 高级使用
```bash
# 使用8个并行工作线程，显示详细性能指标
python3 core_reflow/main.py --branch feature/big-feature --workers 8 --metrics

# 清空缓存后验证，搜索90天内的提交
python3 core_reflow/main.py --mr-id 456 --cache-clear --days 90

# 输出JSON格式结果
python3 core_reflow/main.py --branch feature/auth --output json > results.json
```

## 🎯 核心功能

- ✅ **代码指纹技术** - 基于语义内容生成唯一标识，忽略格式差异
- ✅ **智能匹配算法** - 支持直接合并、Cherry-pick等多种合并场景  
- ✅ **GitLab集成** - 无缝对接GitLab API，自动获取MR信息
- ✅ **交付分支验证** - 自动验证交付分支的所有MR是否进入主线
- ✅ **高性能处理** - 并行处理和智能缓存，快速验证大量MR
- ✅ **多仓库支持** - 同时验证多个项目的MR回流状态
- ✅ **灵活配置** - 支持多项目、多分支的灵活配置
- ✅ **详细报告** - 生成清晰的验证报告，支持多种输出格式


## 💼 使用场景

### **单MR验证**
验证特定MR是否已进入主线分支：
```bash
python3 core_reflow/main.py --mr-id 123 --config config/config.json
```

### **分支批量验证**  
验证分支的所有MR：
```bash
python3 core_reflow/main.py --branch feature/big-feature --config config/config.json
```

### **交付分支验证**（新功能）
自动验证交付分支的所有MR是否进入主线：
```bash
python3 core_reflow/main.py --delivery-branch Release_v1.0.0 --config config/config.json
```

### **多仓库验证**（新功能）
同时验证多个项目：
```bash
python3 core_reflow/main.py --multi-repo --config config/delivery_config.json
```

### **适用团队**
- **开发团队**：验证功能分支是否已合并到主线
- **测试团队**：确认代码变更是否已进入测试环境  
- **运维团队**：跟踪发布分支的代码回流状态
- **管理人员**：监控项目整体的代码合并进度

## 技术栈

- **语言**：Python 3.8+
- **Git集成**：GitPython
- **GitLab集成**：python-gitlab
- **存储**：SQLite + JSON文件

## 🚀 快速验证

```bash
# 1. 复制配置模板
cp config/config.example.json config/config.json

# 2. 编辑配置
vim config/config.json  # 修改GitLab token和项目信息

# 3. 运行验证
python3 core_reflow/main.py --mr-id 123 --config config/config.json
```

## 输出示例

```
================================================================================
MR 回流验证结果
================================================================================

MR #123 - src/service/user.py
状态: 已进入主线
原因: 通过直接合并进入主线分支，匹配提交: a1b2c3d4
建议: 无需操作
----------------------------------------

MR #124 - src/model/product.py
状态: 未进入主线
原因: 在主线分支中未找到匹配的变更
建议: 需要推动合并到主线
----------------------------------------
```

## 📖 扩展阅读

- 💡 **[使用示例](examples/README.md)** - 详细的使用指南和演示代码
- 📋 **[配置说明](config/README.md)** - 配置文件的详细说明和模板
- 📚 **[项目文档](docs/README.md)** - 完整的文档体系和开发指南
- 🧪 **[测试说明](tests/)** - 单元测试和集成测试用例
- 🔧 **[设计文档](docs/design/)** - 系统架构和技术实现方案

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License

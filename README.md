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

## 快速开始

### 1. 运行演示
```bash
# 运行完整演示，了解系统功能
python3 demo_usage.py
```

### 2. 安装依赖
```bash
# 安装必要的Python包
pip install -r requirements.txt
```

### 3. 配置系统
```bash
# 复制配置模板
cp examples/config.example.json config.json

# 编辑配置文件
vim config.json  # 设置GitLab token和项目信息
```

### 4. 运行测试
```bash
# 运行基础功能测试
python3 test_basic.py
```

### 5. 开始使用

#### 基础使用
```bash
# 验证分支的所有MR
python3 core_reflow/main.py --branch your-feature-branch --config config.json

# 验证特定MR
python3 core_reflow/main.py --mr-id 123 --config config.json
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

## 核心功能演示

运行 `python3 demo_usage.py` 可以看到：

- ✅ **指纹生成**：为代码变更生成唯一标识
- ✅ **匹配验证**：智能判断变更是否进入主线
- ✅ **结果输出**：清晰的状态报告和处理建议
- ✅ **配置管理**：灵活的系统配置
- ✅ **错误处理**：完善的异常处理机制

## 目录结构

```
core_reflow/
├── 简化方案设计.md           # 📋 方案设计总览（推荐先读）
├── 代码变更指纹验证方案设计.md  # 📖 详细技术方案
├── 方案设计                  # 🗂️ 原始设计文档
├── examples/                 # 💡 使用示例和配置模板
│   ├── README.md            # 使用指南
│   ├── config.example.json  # 配置模板
│   └── main_example.py      # 主入口示例
├── impl/                    # ⚙️ 实现代码和文档
│   ├── README.md           # 实现指南
│   └── requirements.txt    # 依赖包
├── docs/                    # 📚 API文档和扩展说明
│   └── README.md           # 详细文档
└── README.md               # 本文件
```

## 核心功能

- ✅ **MR状态验证**：判断MR是否已进入 `dev_master` 分支
- ✅ **多路径支持**：支持直接合并、Cherry-pick、多路径合并
- ✅ **智能匹配**：基于代码指纹的精确匹配
- ✅ **多种输出**：控制台、JSON、Markdown格式
- ✅ **配置灵活**：支持自定义忽略规则和搜索范围

## 使用场景

- **开发团队**：验证功能分支是否已合并到主线
- **测试团队**：确认代码变更是否已进入测试环境
- **运维团队**：跟踪发布分支的代码回流状态
- **管理人员**：监控项目整体的代码合并进度

## 技术栈

- **语言**：Python 3.8+
- **Git集成**：GitPython
- **GitLab集成**：python-gitlab
- **存储**：SQLite + JSON文件

## 快速验证

```bash
# 1. 复制配置模板
cp examples/config.example.json config.json

# 2. 编辑配置
vim config.json  # 修改GitLab token和项目信息

# 3. 运行验证
python examples/main_example.py --branch feature/your-branch --config config.json
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

## 扩展阅读

- 📋 **[简化方案设计](简化方案设计.md)** - 核心概念和工作流程
- 📖 **[详细技术方案](代码变更指纹验证方案设计.md)** - 完整的技术实现方案
- 💡 **[使用示例](examples/README.md)** - 详细的使用指南和配置
- ⚙️ **[实现代码](impl/README.md)** - 完整的代码实现和测试
- 📚 **[API文档](docs/README.md)** - 接口说明和扩展功能

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License

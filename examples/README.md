# 示例和演示

本目录包含MR回流验证系统的各种使用示例和演示脚本。

## 📚 **示例文件**

### 1. **basic_usage.py** - 基础使用示例
演示系统的基本功能和组件使用方法。

```bash
# 运行基础使用示例
python3 examples/basic_usage.py
```

**功能演示**:
- 配置管理器使用
- 指纹生成器演示
- 基础组件初始化

### 2. **delivery_branch_demo.py** - 交付分支验证演示
展示如何验证交付分支的所有MR是否进入主线分支。

```bash
# 运行交付分支验证演示
python3 examples/delivery_branch_demo.py
```

**功能演示**:
- GitLab API获取交付分支MR
- 批量验证MR回流状态
- 生成详细验证报告

### 3. **main_example.py** - 主程序使用示例
展示如何通过主程序接口使用各种功能。

```bash
# 运行主程序示例
python3 examples/main_example.py
```

## 🚀 **运行示例**

### **前置条件**
1. 已安装依赖: `pip install -r requirements.txt`
2. 已配置GitLab访问: 编辑 `config/config.json`

### **基础演示**
```bash
# 1. 基础功能演示
python3 examples/basic_usage.py

# 2. 交付分支验证演示
python3 examples/delivery_branch_demo.py

# 3. 主程序功能演示  
python3 examples/main_example.py
```

### **自定义演示**
```bash
# 使用自己的配置运行演示
python3 examples/basic_usage.py --config config/your_config.json

# 指定特定的项目演示
python3 examples/delivery_branch_demo.py --project-id 1752
```

## 📋 **示例说明**

### **适用场景**
- **学习系统功能**: 了解各个组件的作用和用法
- **测试配置**: 验证你的配置是否正确
- **开发参考**: 作为开发新功能的参考代码
- **演示系统**: 向团队展示系统能力

### **自定义建议**
- 复制示例文件并根据你的需求修改
- 调整配置参数来适应你的环境
- 添加自己的业务逻辑和验证规则
- 扩展示例来测试特定的场景

## 🔧 **开发新示例**

如果你想创建新的示例：

1. **复制现有示例**
   ```bash
   cp examples/basic_usage.py examples/your_example.py
   ```

2. **修改导入路径**
   ```python
   import sys
   from pathlib import Path
   project_root = Path(__file__).parent.parent
   sys.path.insert(0, str(project_root))
   ```

3. **添加你的逻辑**
   ```python
   def your_demo_function():
       # 你的演示代码
       pass
   ```

4. **更新README**
   在本文件中添加新示例的说明
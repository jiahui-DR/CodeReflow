# 使用示例

## 配置模板

### config.json

```json
{
  "gitlab": {
    "url": "https://gitlab.yourcompany.com",
    "token": "your-gitlab-token",
    "project_id": 12345
  },
  "git": {
    "repo_path": "/path/to/your/git/repo",
    "target_branch": "dev_master",
    "search_days": 30
  },
  "fingerprint": {
    "ignore_patterns": [
      "^\\s*#.*$",
      "^\\s*$",
      "^\\s*import"
    ]
  }
}
```

## 命令行使用

```bash
# 验证指定分支的所有MR
python main.py --branch feature/my-feature --config config.json

# 验证特定MR
python main.py --mr-id 123 --config config.json

# 输出为JSON格式
python main.py --branch feature/my-feature --output json --config config.json

# 自定义搜索时间范围
python main.py --branch feature/my-feature --days 60 --config config.json
```

## Python API使用

```python
from core_reflow.gitlab.mr_processor import MRProcessor
from core_reflow.git import extractor import ChangeExtractor
from core_reflow.fingerprint.generator import FingerprintGenerator
from core_reflow.git.searcher import MasterBranchSearcher
from core_reflow.core.validator import MatchValidator
from core_reflow.core.outputer import ResultOutputer

# 初始化组件
mr_processor = MRProcessor(gitlab_token, project_id)
change_extractor = ChangeExtractor(repo_path)
fingerprint_gen = FingerprintGenerator()
searcher = MasterBranchSearcher(repo_path)
validator = MatchValidator()
outputer = ResultOutputer()

# 获取MR列表
mrs = mr_processor.get_branch_mrs('feature/my-feature')

# 处理每个MR
all_results = []
for mr in mrs:
    # 提取变更
    changes = change_extractor.extract_changes(mr)

    # 生成指纹
    fingerprints = fingerprint_gen.generate(changes)

    # 在主线分支中搜索
    search_results = searcher.search_changes_in_master(fingerprints)

    # 验证结果
    validated_results = validator.validate_results(search_results)

    all_results.extend(validated_results)

# 输出结果
outputer.output_results(all_results, 'console')
```

## 输出示例

### 控制台输出
```
================================================================================
MR 回流验证结果
================================================================================

MR #123 - src/service/user.py
状态: 已进入主线
原因: 通过直接合并进入主线分支，匹配提交: a1b2c3d4
建议: 无需操作
匹配提交: a1b2c3d4
置信度: 1.00
----------------------------------------

MR #124 - src/model/product.py
状态: 未进入主线
原因: 在主线分支中未找到匹配的变更
建议: 需要推动合并到主线
----------------------------------------
```

### JSON输出
```json
[
  {
    "mr_id": 123,
    "fingerprint": "a1b2c3d4e5f67890",
    "file_path": "src/service/user.py",
    "matched": true,
    "match_commit": "a1b2c3d4e5f678901234567890abcdef12345678",
    "match_type": "direct_merge",
    "confidence": 1.0,
    "conclusion": "已进入主线",
    "reason": "通过直接合并进入主线分支，匹配提交: a1b2c3d4",
    "recommendation": "无需操作"
  }
]
```

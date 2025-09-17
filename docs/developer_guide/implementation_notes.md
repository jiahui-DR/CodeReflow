# 实现代码

## 项目结构

```
core_reflow/
├── gitlab/
│   ├── client.py         # GitLab API客户端
│   └── mr_processor.py   # MR处理器
├── git/
│   ├── extractor.py      # 变更提取器
│   └── searcher.py       # 主线分支搜索器
├── fingerprint/
│   └── generator.py      # 指纹生成器
├── core/
│   ├── validator.py      # 匹配验证器
│   └── outputer.py       # 结果输出器
├── utils/
│   ├── config.py         # 配置管理
│   └── helpers.py        # 工具函数
├── tests/
│   ├── test_mr_fetch.py  # MR获取测试
│   ├── test_fingerprint.py # 指纹生成测试
│   └── test_integration.py # 集成测试
├── config.example.json   # 配置示例
├── requirements.txt      # 依赖包
└── main.py              # 主入口
```

## 核心组件实现

### 1. MR处理器

```python
# gitlab/mr_processor.py
import gitlab

class MRProcessor:
    def __init__(self, gitlab_token, project_id, gitlab_url='https://gitlab.com'):
        self.gitlab = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
        self.project = self.gitlab.projects.get(project_id)

    def get_branch_mrs(self, source_branch, target_branch='dev_master'):
        """获取指定分支的MR列表"""
        mrs = self.project.mergerequests.list(
            source_branch=source_branch,
            target_branch=target_branch,
            state='merged'  # 只处理已合并的MR
        )
        return [self._enrich_mr(mr) for mr in mrs]

    def _enrich_mr(self, mr):
        """丰富MR信息"""
        return {
            'id': mr.iid,
            'title': mr.title,
            'description': mr.description,
            'source_branch': mr.source_branch,
            'target_branch': mr.target_branch,
            'merge_commit_sha': mr.merge_commit_sha,
            'state': mr.state,
            'author': mr.author['username']
        }
```

### 2. 变更提取器

```python
# git/extractor.py
import git

class ChangeExtractor:
    def __init__(self, repo_path):
        self.repo = git.Repo(repo_path)

    def extract_changes(self, mr_info):
        """从MR中提取代码变更"""
        # 方法1：通过merge commit获取变更
        if mr_info.get('merge_commit_sha'):
            commit = self.repo.commit(mr_info['merge_commit_sha'])
            return self._get_commit_changes(commit)

        # 方法2：通过MR的源分支和目标分支对比
        return self._get_branch_diff(
            mr_info['source_branch'],
            mr_info['target_branch']
        )

    def _get_commit_changes(self, commit):
        """获取提交的变更内容"""
        if len(commit.parents) == 0:
            # 初始提交
            return self._get_initial_commit_changes(commit)
        else:
            # 普通提交
            parent = commit.parents[0]
            diff = parent.diff(commit, create_patch=True)
            return self._parse_diff(diff)

    def _parse_diff(self, diff):
        """解析diff内容"""
        changes = []
        for patch in diff:
            if patch.a_path.endswith(('.py', '.java', '.js', '.ts')):  # 只处理代码文件
                changes.append({
                    'file_path': patch.a_path,
                    'change_type': self._detect_change_type(patch),
                    'diff_content': patch.diff.decode('utf-8', errors='ignore')
                })
        return changes
```

### 3. 指纹生成器

```python
# fingerprint/generator.py
import hashlib
import re

class FingerprintGenerator:
    def __init__(self):
        self.ignore_patterns = [
            r'^\s*#.*$',      # 注释
            r'^\s*$',         # 空行
            r'^\s*import',    # 导入语句
            r'^\s*from.*import', # 导入语句
        ]

    def generate(self, changes):
        """为MR变更生成指纹"""
        fingerprints = []

        for change in changes:
            # 1. 提取有意义的变更行
            meaningful_lines = self._extract_meaningful_lines(change['diff_content'])

            if not meaningful_lines:
                continue

            # 2. 生成内容哈希
            content_hash = hashlib.sha256(
                ''.join(meaningful_lines).encode()
            ).hexdigest()[:16]

            # 3. 生成文件级指纹
            fingerprint = {
                'fingerprint': content_hash,
                'mr_id': change.get('mr_id'),
                'file_path': change['file_path'],
                'change_type': change['change_type'],
                'line_count': len(meaningful_lines),
                'content_preview': ''.join(meaningful_lines[:3])  # 前3行预览
            }

            fingerprints.append(fingerprint)

        return fingerprints

    def _extract_meaningful_lines(self, diff_content):
        """提取有意义的变更行"""
        lines = diff_content.split('\n')
        meaningful_lines = []

        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                # 新增行
                content = line[1:].strip()
                if content and not self._is_ignored_line(content):
                    meaningful_lines.append(content)
            elif line.startswith('-') and not line.startswith('---'):
                # 删除行
                content = line[1:].strip()
                if content and not self._is_ignored_line(content):
                    meaningful_lines.append(content)

        return meaningful_lines

    def _is_ignored_line(self, line):
        """判断是否为忽略行"""
        for pattern in self.ignore_patterns:
            if re.match(pattern, line):
                return True
        return False
```

### 4. 主线分支搜索器

```python
# git/searcher.py
import git
from datetime import datetime, timedelta

class MasterBranchSearcher:
    def __init__(self, repo_path, target_branch='dev_master'):
        self.repo = git.Repo(repo_path)
        self.target_branch = target_branch

    def search_changes_in_master(self, mr_fingerprints, days_back=30):
        """在主线分支中搜索MR变更的匹配"""
        # 获取主线分支最近的提交
        master_commits = self._get_recent_commits(days_back)

        results = []
        for fingerprint in mr_fingerprints:
            match_result = self._search_fingerprint_in_commits(fingerprint, master_commits)
            results.append({
                'mr_id': fingerprint.get('mr_id'),
                'fingerprint': fingerprint['fingerprint'],
                'file_path': fingerprint['file_path'],
                'matched': match_result['matched'],
                'match_commit': match_result.get('commit'),
                'match_type': match_result.get('type', 'none'),
                'confidence': match_result['confidence']
            })

        return results

    def _get_recent_commits(self, days_back):
        """获取主线分支最近的提交"""
        since_date = datetime.now() - timedelta(days=days_back)

        # 获取目标分支的提交
        commits = list(self.repo.iter_commits(
            self.target_branch,
            since=since_date
        ))

        return commits

    def _search_fingerprint_in_commits(self, fingerprint, commits):
        """在提交列表中搜索指纹匹配"""
        for commit in commits:
            # 方法1：直接比较merge commit
            if hasattr(commit, 'merge_commit_sha') and commit.merge_commit_sha:
                if self._check_commit_fingerprint(commit, fingerprint):
                    return {
                        'matched': True,
                        'commit': commit.hexsha,
                        'type': 'direct_merge',
                        'confidence': 1.0
                    }

            # 方法2：检查commit的变更内容
            if self._check_commit_fingerprint(commit, fingerprint):
                return {
                    'matched': True,
                    'commit': commit.hexsha,
                    'type': 'content_match',
                    'confidence': 0.9
                }

        return {
            'matched': False,
            'confidence': 0.0
        }

    def _check_commit_fingerprint(self, commit, fingerprint):
        """检查提交是否包含匹配的指纹"""
        try:
            # 获取提交的变更
            if len(commit.parents) == 0:
                # 初始提交
                diff = commit.diff(create_patch=True)
            else:
                # 普通提交
                parent = commit.parents[0]
                diff = parent.diff(commit, create_patch=True)

            # 生成该提交的指纹
            commit_changes = self._parse_commit_diff(diff)
            commit_fingerprints = self._generate_quick_fingerprints(commit_changes)

            # 比较指纹
            for commit_fp in commit_fingerprints:
                if commit_fp['fingerprint'] == fingerprint['fingerprint']:
                    return True

        except Exception as e:
            print(f"Error checking commit {commit.hexsha}: {e}")

        return False
```

### 5. 匹配验证器

```python
# core/validator.py
class MatchValidator:
    def __init__(self):
        self.confidence_threshold = 0.8

    def validate_results(self, search_results):
        """验证搜索结果并生成最终结论"""
        validated_results = []

        for result in search_results:
            conclusion = self._determine_conclusion(result)

            validated_result = {
                **result,
                'conclusion': conclusion['status'],
                'reason': conclusion['reason'],
                'recommendation': conclusion['recommendation']
            }

            validated_results.append(validated_result)

        return validated_results

    def _determine_conclusion(self, result):
        """根据匹配结果确定结论"""
        if result['matched'] and result['confidence'] >= self.confidence_threshold:
            if result['match_type'] == 'direct_merge':
                return {
                    'status': '已进入主线',
                    'reason': f'通过直接合并进入主线分支，匹配提交: {result["match_commit"][:8]}',
                    'recommendation': '无需操作'
                }
            elif result['match_type'] == 'content_match':
                return {
                    'status': '已进入主线',
                    'reason': f'通过内容匹配确认已进入主线分支，匹配提交: {result["match_commit"][:8]}',
                    'recommendation': '无需操作'
                }

        elif result['matched'] and result['confidence'] >= 0.5:
            return {
                'status': '疑似已进入',
                'reason': f'找到相似匹配，但置信度较低 ({result["confidence"]:.2f})',
                'recommendation': '建议人工确认'
            }

        else:
            return {
                'status': '未进入主线',
                'reason': '在主线分支中未找到匹配的变更',
                'recommendation': '需要推动合并到主线'
            }
```

### 6. 结果输出器

```python
# core/outputer.py
import json

class ResultOutputer:
    def __init__(self):
        pass

    def output_results(self, validated_results, output_format='console'):
        """输出验证结果"""
        if output_format == 'console':
            self._output_to_console(validated_results)
        elif output_format == 'json':
            return self._output_to_json(validated_results)
        elif output_format == 'markdown':
            return self._output_to_markdown(validated_results)

    def _output_to_console(self, results):
        """控制台输出"""
        print("\n" + "="*80)
        print("MR 回流验证结果")
        print("="*80)

        for result in results:
            print(f"\nMR #{result['mr_id']} - {result['file_path']}")
            print(f"状态: {result['conclusion']}")
            print(f"原因: {result['reason']}")
            print(f"建议: {result['recommendation']}")
            if result['matched']:
                print(f"匹配提交: {result['match_commit'][:8]}")
                print(f"置信度: {result['confidence']:.2f}")
            print("-" * 40)

    def _output_to_json(self, results):
        """JSON格式输出"""
        return json.dumps(results, indent=2, ensure_ascii=False)

    def _output_to_markdown(self, results):
        """Markdown格式输出"""
        md = "# MR 回流验证报告\n\n"
        md += "| MR ID | 文件路径 | 状态 | 原因 | 建议 |\n"
        md += "|-------|----------|------|------|------|\n"

        for result in results:
            md += f"| {result['mr_id']} | {result['file_path']} | {result['conclusion']} | {result['reason']} | {result['recommendation']} |\n"

        return md
```

## 依赖包

```txt
# requirements.txt
GitPython>=3.1.0
python-gitlab>=3.0.0
```

## 测试场景

### 场景1：直接合并
```
feature-branch: A -> B -> C
main-branch:    X -> Y -> (merge C)
```
**预期结果**：能够识别C的变更已进入main

### 场景2：Cherry-pick
```
feature-branch: A -> B -> C
main-branch:    X -> Y -> (cherry-pick C) -> Z
```
**预期结果**：能够识别C的变更已进入main

### 场景3：多路径合并
```
feature/A: A1 -> A2
feature/B: B1 -> B2 -> (merge A2)
main:      M1 -> M2 -> (merge B2)
```
**预期结果**：能够识别A1的变更通过多路径进入main

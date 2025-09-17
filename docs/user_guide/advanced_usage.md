# 高级用法指南

本指南介绍 Core Reflow 的高级功能和使用技巧，帮助您在复杂场景下高效使用系统。

## 🎯 高级验证场景

### 1. 大规模批量验证

处理包含大量 MR 的分支或项目：

```bash
# 增加并行度和超时时间
core-reflow --branch feature/large-refactor \
  --workers 16 \
  --days 90 \
  --config large-project.json

# 启用文件缓存减少重复计算
cat > large-project.json << EOF
{
  "performance": {
    "max_workers": 16,
    "chunk_size": 20,
    "timeout": 1800
  },
  "cache": {
    "backend": "file",
    "cache_dir": "/tmp/large_cache",
    "default_ttl": 86400
  }
}
EOF
```

### 2. 精确时间范围验证

验证特定时间段的变更：

```python
# 使用 Python API 进行精确时间控制
from datetime import datetime, timedelta
from core_reflow.main import MRReflowValidator

validator = MRReflowValidator('config.json')

# 设置精确的时间范围
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31)

# 自定义搜索逻辑
validator.searcher.set_time_range(start_date, end_date)
validator.validate_branch('feature/january-features')
```

### 3. 条件验证和过滤

基于 MR 属性进行条件验证：

```python
# 自定义 MR 过滤器
def filter_mrs(mrs):
    """只验证特定作者或标签的 MR"""
    filtered = []
    for mr in mrs:
        # 只验证特定作者
        if mr.get('author', {}).get('username') in ['dev1', 'dev2']:
            filtered.append(mr)
        # 只验证包含特定标签的 MR
        elif 'critical' in mr.get('labels', []):
            filtered.append(mr)
    return filtered

# 应用自定义过滤器
validator.mr_processor.filter_function = filter_mrs
validator.validate_branch('feature/filtered-validation')
```

## 🔄 交付分支高级验证

### 1. 多版本交付验证

验证多个版本的交付分支：

```json
{
  "delivery_validation": {
    "versions": [
      {
        "name": "v1.0.0",
        "delivery_branch": "delivery/v1.0.0",
        "target_branch": "release/v1.0.x",
        "validation_rules": {
          "require_all_mrs": true,
          "allow_documentation_only": false
        }
      },
      {
        "name": "v2.0.0", 
        "delivery_branch": "delivery/v2.0.0",
        "target_branch": "main",
        "validation_rules": {
          "require_all_mrs": true,
          "similarity_threshold": 0.95
        }
      }
    ]
  }
}
```

```bash
# 验证多个版本
for version in v1.0.0 v2.0.0; do
  echo "验证版本: $version"
  core-reflow-cli --delivery-branch "delivery/$version" \
    --config delivery-config.json
done
```

### 2. 分阶段验证策略

```python
# 分阶段验证实现
class StageValidation:
    def __init__(self, config_file):
        self.validator = MRReflowValidator(config_file)
    
    def validate_by_stages(self, delivery_branch):
        """分阶段验证交付分支"""
        
        # 阶段1: 快速预检
        print("🔍 阶段1: 快速预检...")
        quick_results = self.quick_validation(delivery_branch)
        
        if not quick_results['passed']:
            print("❌ 快速预检失败，停止验证")
            return False
        
        # 阶段2: 详细验证
        print("🔍 阶段2: 详细验证...")
        detailed_results = self.detailed_validation(delivery_branch)
        
        # 阶段3: 生成报告
        print("📊 阶段3: 生成报告...")
        self.generate_report(quick_results, detailed_results)
        
        return detailed_results['passed']
    
    def quick_validation(self, branch):
        """快速验证：只检查关键MR"""
        # 设置较小的搜索范围
        self.validator.search_days = 7
        # 只验证标记为关键的MR
        return self.validator.validate_branch(branch)
    
    def detailed_validation(self, branch):
        """详细验证：完整检查"""
        # 恢复完整搜索范围
        self.validator.search_days = 30
        return self.validator.validate_branch(branch)

# 使用分阶段验证
stage_validator = StageValidation('config.json')
stage_validator.validate_by_stages('delivery/v1.0.0')
```

## 🏗️ 自定义验证逻辑

### 1. 自定义指纹生成器

```python
from core_reflow.fingerprint.generator import FingerprintGenerator

class CustomFingerprintGenerator(FingerprintGenerator):
    """自定义指纹生成器"""
    
    def generate_file_fingerprint(self, file_path, content):
        """自定义文件指纹生成逻辑"""
        fingerprint = super().generate_file_fingerprint(file_path, content)
        
        # 添加自定义元数据
        if file_path.endswith('.py'):
            # Python 文件：提取类名和函数名
            fingerprint['python_symbols'] = self.extract_python_symbols(content)
        elif file_path.endswith('.js'):
            # JavaScript 文件：提取函数和类
            fingerprint['js_symbols'] = self.extract_js_symbols(content)
        
        return fingerprint
    
    def extract_python_symbols(self, content):
        """提取 Python 符号"""
        import ast
        try:
            tree = ast.parse(content)
            symbols = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(f"function:{node.name}")
                elif isinstance(node, ast.ClassDef):
                    symbols.append(f"class:{node.name}")
            return symbols
        except:
            return []

# 使用自定义生成器
validator = MRReflowValidator('config.json')
validator.fingerprint_gen = CustomFingerprintGenerator([])
```

### 2. 自定义匹配验证器

```python
from core_reflow.core.validator import MatchValidator

class SmartMatchValidator(MatchValidator):
    """智能匹配验证器"""
    
    def validate_match(self, search_result):
        """智能匹配验证"""
        base_result = super().validate_match(search_result)
        
        # 添加额外的验证逻辑
        confidence = base_result.get('confidence', 0)
        
        # 文件类型权重调整
        file_path = search_result.get('file_path', '')
        if file_path.endswith(('.py', '.java', '.cpp')):
            # 代码文件提高权重
            confidence *= 1.2
        elif file_path.endswith(('.md', '.txt')):
            # 文档文件降低权重
            confidence *= 0.8
        
        # 变更大小权重调整
        line_count = search_result.get('line_count', 0)
        if line_count > 50:
            # 大变更提高可信度
            confidence *= 1.1
        elif line_count < 5:
            # 小变更降低可信度
            confidence *= 0.9
        
        base_result['confidence'] = min(confidence, 1.0)
        base_result['matched'] = confidence >= 0.85  # 调整阈值
        
        return base_result

# 应用自定义验证器
validator.validator = SmartMatchValidator()
```

## 📊 高级输出和报告

### 1. 自定义报告生成

```python
from core_reflow.core.outputer import ResultOutputer
import json
from datetime import datetime

class AdvancedOutputer(ResultOutputer):
    """高级输出器"""
    
    def generate_executive_summary(self, results):
        """生成执行摘要"""
        total = len(results)
        matched = sum(1 for r in results if r.get('matched'))
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_mrs': total,
                'matched_mrs': matched,
                'unmatched_mrs': total - matched,
                'success_rate': f"{matched/total*100:.1f}%" if total > 0 else "0%"
            },
            'risk_assessment': self.assess_risk(results),
            'recommendations': self.generate_recommendations(results)
        }
        
        return summary
    
    def assess_risk(self, results):
        """风险评估"""
        unmatched = [r for r in results if not r.get('matched')]
        
        if not unmatched:
            return {'level': 'LOW', 'description': '所有变更已验证'}
        elif len(unmatched) / len(results) < 0.1:
            return {'level': 'MEDIUM', 'description': '少量变更未验证'}
        else:
            return {'level': 'HIGH', 'description': '大量变更未验证'}
    
    def output_dashboard_format(self, results):
        """输出仪表板格式"""
        summary = self.generate_executive_summary(results)
        
        print("📊 MR 回流验证仪表板")
        print("=" * 50)
        print(f"🕐 验证时间: {summary['timestamp']}")
        print(f"📈 成功率: {summary['overview']['success_rate']}")
        print(f"⚠️  风险等级: {summary['risk_assessment']['level']}")
        print(f"💡 建议: {', '.join(summary['recommendations'])}")

# 使用高级输出器
validator.outputer = AdvancedOutputer()
```

### 2. 集成外部报告系统

```python
import requests

class IntegratedReporter:
    """集成报告器"""
    
    def __init__(self, webhook_url, slack_token=None):
        self.webhook_url = webhook_url
        self.slack_token = slack_token
    
    def send_to_dashboard(self, results):
        """发送到监控仪表板"""
        payload = {
            'timestamp': datetime.now().isoformat(),
            'service': 'core-reflow',
            'metrics': {
                'total_mrs': len(results),
                'success_rate': self.calculate_success_rate(results)
            }
        }
        
        requests.post(self.webhook_url, json=payload)
    
    def send_slack_notification(self, results):
        """发送 Slack 通知"""
        if not self.slack_token:
            return
        
        success_rate = self.calculate_success_rate(results)
        
        if success_rate < 0.8:
            emoji = "🚨"
            color = "danger"
        elif success_rate < 0.95:
            emoji = "⚠️"
            color = "warning"
        else:
            emoji = "✅"
            color = "good"
        
        message = {
            'text': f"{emoji} MR 回流验证报告",
            'attachments': [{
                'color': color,
                'fields': [
                    {'title': '成功率', 'value': f"{success_rate:.1%}", 'short': True},
                    {'title': '总 MR 数', 'value': str(len(results)), 'short': True}
                ]
            }]
        }
        
        requests.post(
            'https://slack.com/api/chat.postMessage',
            headers={'Authorization': f'Bearer {self.slack_token}'},
            json=message
        )

# 集成使用
reporter = IntegratedReporter(
    webhook_url='https://monitoring.company.com/webhook',
    slack_token='xoxb-your-slack-token'
)

# 验证完成后发送报告
results = validator.validate_branch('feature/integration')
reporter.send_to_dashboard(results)
reporter.send_slack_notification(results)
```

## 🔧 性能优化技巧

### 1. 缓存策略优化

```python
# 多层缓存实现
from core_reflow.utils.cache import CacheManager, MemoryCache, FileCache

class MultiLevelCache:
    """多级缓存"""
    
    def __init__(self):
        # L1: 内存缓存（快速）
        self.l1_cache = MemoryCache(max_size=500, default_ttl=1800)
        # L2: 文件缓存（持久）
        self.l2_cache = FileCache(cache_dir='.cache', default_ttl=86400)
    
    def get(self, key):
        # 先查 L1
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # 再查 L2
        value = self.l2_cache.get(key)
        if value is not None:
            # 回写到 L1
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key, value, ttl=None):
        # 同时写入两级缓存
        self.l1_cache.set(key, value, ttl)
        self.l2_cache.set(key, value, ttl)

# 应用多级缓存
validator.cache_manager = CacheManager(MultiLevelCache())
```

### 2. 智能并行策略

```python
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed

class AdaptiveParallelProcessor:
    """自适应并行处理器"""
    
    def __init__(self):
        # 根据系统资源动态调整
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 保守策略：不超过 CPU 核心数，考虑内存限制
        max_workers = min(cpu_count, int(memory_gb / 2), 16)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_with_backpressure(self, tasks, processor_func):
        """带反压的处理"""
        futures = []
        results = []
        
        # 提交初始批次
        for i, task in enumerate(tasks[:self.executor._max_workers]):
            future = self.executor.submit(processor_func, task)
            futures.append((future, i))
        
        # 动态提交剩余任务
        task_index = self.executor._max_workers
        
        for future, original_index in as_completed([f for f, _ in futures]):
            results.append((original_index, future.result()))
            
            # 提交下一个任务
            if task_index < len(tasks):
                new_future = self.executor.submit(processor_func, tasks[task_index])
                futures.append((new_future, task_index))
                task_index += 1
        
        return sorted(results, key=lambda x: x[0])

# 使用自适应处理器
validator.parallel_processor = AdaptiveParallelProcessor()
```

### 3. 增量验证

```python
class IncrementalValidator:
    """增量验证器"""
    
    def __init__(self, config_file):
        self.validator = MRReflowValidator(config_file)
        self.state_file = '.core_reflow_state.json'
    
    def load_previous_state(self):
        """加载上次验证状态"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'last_verified_mr': 0, 'verified_mrs': set()}
    
    def save_state(self, state):
        """保存验证状态"""
        # 转换 set 为 list 用于 JSON 序列化
        state_copy = state.copy()
        state_copy['verified_mrs'] = list(state['verified_mrs'])
        
        with open(self.state_file, 'w') as f:
            json.dump(state_copy, f)
    
    def incremental_validate_branch(self, branch_name):
        """增量验证分支"""
        state = self.load_previous_state()
        verified_mrs = set(state.get('verified_mrs', []))
        
        # 获取所有 MR
        all_mrs = self.validator.mr_processor.get_branch_mrs(branch_name)
        
        # 过滤出需要验证的 MR
        new_mrs = [mr for mr in all_mrs if mr['id'] not in verified_mrs]
        
        if not new_mrs:
            print("✅ 没有新的 MR 需要验证")
            return
        
        print(f"🔍 发现 {len(new_mrs)} 个新的 MR，开始增量验证...")
        
        # 只验证新的 MR
        for mr in new_mrs:
            try:
                results = self.validator.validate_mr(mr['id'])
                verified_mrs.add(mr['id'])
                print(f"✅ MR #{mr['id']} 验证完成")
            except Exception as e:
                print(f"❌ MR #{mr['id']} 验证失败: {e}")
        
        # 更新状态
        state['verified_mrs'] = verified_mrs
        state['last_update'] = datetime.now().isoformat()
        self.save_state(state)

# 使用增量验证
incremental = IncrementalValidator('config.json')
incremental.incremental_validate_branch('feature/large-feature')
```

## 🔍 监控和诊断

### 1. 性能监控

```python
import time
import psutil
from contextlib import contextmanager

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    @contextmanager
    def measure_performance(self, operation_name):
        """测量操作性能"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            self.metrics[operation_name] = {
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_report(self):
        """获取性能报告"""
        total_time = sum(m['duration'] for m in self.metrics.values())
        max_memory = max(m['memory_delta'] for m in self.metrics.values())
        
        return {
            'total_operations': len(self.metrics),
            'total_duration': total_time,
            'max_memory_usage': max_memory,
            'operations': self.metrics
        }

# 集成性能监控
monitor = PerformanceMonitor()

with monitor.measure_performance('gitlab_api_calls'):
    mrs = validator.mr_processor.get_branch_mrs('feature/test')

with monitor.measure_performance('fingerprint_generation'):
    # 指纹生成操作
    pass

# 查看性能报告
print(json.dumps(monitor.get_performance_report(), indent=2))
```

### 2. 健康检查

```python
class HealthChecker:
    """健康检查器"""
    
    def __init__(self, validator):
        self.validator = validator
    
    def check_gitlab_connectivity(self):
        """检查 GitLab 连接"""
        try:
            project = self.validator.mr_processor._gitlab.projects.get(
                self.validator.mr_processor.project_id
            )
            return {'status': 'healthy', 'project_name': project.name}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_git_repository(self):
        """检查 Git 仓库"""
        try:
            repo_path = self.validator.config.get('git.repo_path')
            if not os.path.exists(repo_path):
                return {'status': 'unhealthy', 'error': 'Repository path not found'}
            
            # 检查 Git 仓库状态
            repo = git.Repo(repo_path)
            return {
                'status': 'healthy',
                'current_branch': repo.active_branch.name,
                'commit_count': repo.git.rev_list('--count', 'HEAD')
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_cache_status(self):
        """检查缓存状态"""
        try:
            stats = self.validator.cache_manager.get_stats()
            return {
                'status': 'healthy',
                'hit_rate': stats['hit_rate'],
                'size': stats['size']
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def full_health_check(self):
        """完整健康检查"""
        return {
            'gitlab': self.check_gitlab_connectivity(),
            'git_repository': self.check_git_repository(),
            'cache': self.check_cache_status(),
            'timestamp': datetime.now().isoformat()
        }

# 执行健康检查
health_checker = HealthChecker(validator)
health_report = health_checker.full_health_check()
print(json.dumps(health_report, indent=2))
```

## 🚀 自动化和集成

### 1. CI/CD 集成

```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy
  - validate

mr_reflow_validation:
  stage: validate
  script:
    - pip install core-reflow
    - |
      if [ "$CI_PIPELINE_SOURCE" = "merge_request_event" ]; then
        # 验证当前 MR
        core-reflow --mr-id $CI_MERGE_REQUEST_IID --config ci-config.json
      else
        # 验证整个分支
        core-reflow --branch $CI_COMMIT_REF_NAME --config ci-config.json
      fi
  artifacts:
    reports:
      junit: validation-report.xml
    when: always
  only:
    - merge_requests
    - main
    - develop
```

### 2. 定时验证

```python
# 定时验证脚本
import schedule
import time

def scheduled_validation():
    """定时执行验证"""
    branches_to_validate = [
        'develop',
        'release/current',
        'delivery/latest'
    ]
    
    for branch in branches_to_validate:
        try:
            print(f"🔍 开始验证分支: {branch}")
            validator = MRReflowValidator('scheduled-config.json')
            results = validator.validate_branch(branch)
            
            # 发送报告
            send_daily_report(branch, results)
            
        except Exception as e:
            print(f"❌ 验证失败 {branch}: {e}")
            send_error_alert(branch, str(e))

# 设置定时任务
schedule.every().day.at("09:00").do(scheduled_validation)
schedule.every().hour.do(lambda: print("💓 系统运行正常"))

# 运行调度器
while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Webhook 集成

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/gitlab', methods=['POST'])
def gitlab_webhook():
    """GitLab Webhook 处理"""
    data = request.json
    
    # 只处理 MR 事件
    if data.get('object_kind') != 'merge_request':
        return jsonify({'status': 'ignored'})
    
    mr_info = data.get('object_attributes', {})
    
    # 只处理已合并的 MR
    if mr_info.get('state') != 'merged':
        return jsonify({'status': 'not_merged'})
    
    try:
        # 异步执行验证
        from threading import Thread
        
        def async_validate():
            validator = MRReflowValidator('webhook-config.json')
            results = validator.validate_mr(mr_info['id'])
            
            # 发送结果通知
            send_webhook_result(mr_info, results)
        
        Thread(target=async_validate).start()
        
        return jsonify({'status': 'queued'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## 📈 大规模部署

### 1. 分布式验证

```python
import redis
from rq import Queue, Worker

# Redis 任务队列
redis_conn = redis.Redis(host='localhost', port=6379, db=0)
task_queue = Queue('mr_validation', connection=redis_conn)

def validate_mr_task(mr_id, config_path):
    """验证 MR 的异步任务"""
    validator = MRReflowValidator(config_path)
    return validator.validate_mr(mr_id)

# 提交验证任务
def submit_batch_validation(mr_ids, config_path):
    """提交批量验证任务"""
    jobs = []
    for mr_id in mr_ids:
        job = task_queue.enqueue(
            validate_mr_task,
            mr_id,
            config_path,
            timeout=300
        )
        jobs.append(job)
    return jobs

# Worker 进程
if __name__ == '__main__':
    worker = Worker(['mr_validation'], connection=redis_conn)
    worker.work()
```

### 2. 微服务化

```python
# FastAPI 微服务
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Core Reflow API")

class ValidationRequest(BaseModel):
    branch_name: str = None
    mr_id: int = None
    config: dict = None

@app.post("/api/v1/validate")
async def submit_validation(
    request: ValidationRequest,
    background_tasks: BackgroundTasks
):
    """提交验证请求"""
    task_id = generate_task_id()
    
    background_tasks.add_task(
        execute_validation,
        task_id,
        request
    )
    
    return {"task_id": task_id, "status": "submitted"}

@app.get("/api/v1/validation/{task_id}")
async def get_validation_status(task_id: str):
    """获取验证状态"""
    return get_task_status(task_id)

# 启动服务
# uvicorn main:app --host 0.0.0.0 --port 8000
```

## 💡 最佳实践总结

### 1. 性能优化

- 使用文件缓存进行持久化缓存
- 根据机器资源调整并行度
- 实施增量验证减少重复工作
- 使用异步处理提高吞吐量

### 2. 监控和报警

- 集成性能监控和健康检查
- 设置自动报警机制
- 定期生成验证报告
- 跟踪关键指标趋势

### 3. 可扩展性

- 采用微服务架构支持水平扩展
- 使用消息队列处理大批量任务
- 实现配置中心统一管理
- 支持多环境部署

### 4. 安全性

- 使用环境变量存储敏感信息
- 实施访问控制和权限管理
- 定期轮换访问令牌
- 审计验证操作日志

通过这些高级功能和技巧，您可以在各种复杂场景下高效使用 Core Reflow 系统。

#!/usr/bin/env python3
"""
交付分支MR验证器设计方案
自动获取交付分支的所有MR，并验证其是否进入主线分支
"""

class DeliveryBranchMRValidator:
    """
    交付分支MR验证器 - 新的核心功能设计
    
    功能描述:
    1. 连接到指定的GitLab仓库
    2. 获取指定交付分支的所有合并MR
    3. 批量验证这些MR是否已进入主线分支
    4. 生成详细的验证报告
    """
    
    def __init__(self, config):
        """
        初始化验证器
        
        配置结构建议:
        {
            "repositories": [
                {
                    "name": "项目A",
                    "gitlab_url": "https://gitlab.company.com",
                    "gitlab_token": "token1",
                    "project_id": 123,
                    "repo_path": "/path/to/local/repo",
                    "delivery_branch": "release/v1.0.0",  # 交付分支
                    "master_branch": "dev_master",        # 主线分支
                    "search_days": 90                     # 搜索范围
                },
                {
                    "name": "项目B", 
                    "gitlab_url": "https://gitlab.company.com",
                    "gitlab_token": "token2", 
                    "project_id": 456,
                    "repo_path": "/path/to/another/repo",
                    "delivery_branch": "release/v2.0.0",
                    "master_branch": "main",
                    "search_days": 60
                }
            ]
        }
        """
        self.repositories = config.get('repositories', [])
        
    def validate_all_repositories(self):
        """验证所有配置的仓库"""
        results = {}
        
        for repo_config in self.repositories:
            print(f"🔍 开始验证仓库: {repo_config['name']}")
            
            # 验证单个仓库
            repo_result = self.validate_single_repository(repo_config)
            results[repo_config['name']] = repo_result
            
        return results
    
    def validate_single_repository(self, repo_config):
        """验证单个仓库的交付分支MR"""
        
        # 1. 连接GitLab和Git仓库
        gitlab_client = self._connect_gitlab(repo_config)
        git_repo = self._connect_git_repo(repo_config['repo_path'])
        
        # 2. 获取交付分支的所有MR
        delivery_mrs = self._get_delivery_branch_mrs(
            gitlab_client, 
            repo_config['delivery_branch']
        )
        
        print(f"📋 找到 {len(delivery_mrs)} 个交付分支MR")
        
        # 3. 逐一验证MR是否在主线分支
        validation_results = []
        
        for mr in delivery_mrs:
            print(f"🔍 验证MR #{mr['iid']}: {mr['title'][:50]}...")
            
            # 提取MR变更
            changes = self._extract_mr_changes(git_repo, mr)
            
            if not changes:
                result = {
                    'mr_id': mr['iid'],
                    'title': mr['title'],
                    'status': 'NO_CHANGES',
                    'message': '未找到代码变更'
                }
            else:
                # 生成指纹
                fingerprints = self._generate_fingerprints(changes)
                
                # 在主线分支中搜索
                match_results = self._search_in_master_branch(
                    git_repo, 
                    fingerprints,
                    repo_config['master_branch'],
                    repo_config['search_days']
                )
                
                # 验证匹配结果
                is_merged = self._validate_merge_status(match_results)
                
                result = {
                    'mr_id': mr['iid'],
                    'title': mr['title'],
                    'source_branch': mr.get('source_branch'),
                    'merged_at': mr.get('merged_at'),
                    'status': 'MERGED' if is_merged else 'NOT_MERGED',
                    'changes_count': len(changes),
                    'fingerprints_count': len(fingerprints),
                    'match_confidence': self._calculate_confidence(match_results),
                    'details': match_results
                }
            
            validation_results.append(result)
            
        return {
            'repository': repo_config['name'],
            'delivery_branch': repo_config['delivery_branch'], 
            'master_branch': repo_config['master_branch'],
            'total_mrs': len(delivery_mrs),
            'merged_count': len([r for r in validation_results if r['status'] == 'MERGED']),
            'not_merged_count': len([r for r in validation_results if r['status'] == 'NOT_MERGED']),
            'no_changes_count': len([r for r in validation_results if r['status'] == 'NO_CHANGES']),
            'results': validation_results
        }
    
    def _get_delivery_branch_mrs(self, gitlab_client, delivery_branch):
        """获取指定交付分支的所有MR"""
        
        # 方案1: 获取以delivery_branch为target_branch的MR
        target_branch_mrs = gitlab_client.project.mergerequests.list(
            state='merged',
            target_branch=delivery_branch,
            order_by='updated_at',
            sort='desc',
            get_all=True
        )
        
        # 方案2: 获取以delivery_branch为source_branch的MR  
        source_branch_mrs = gitlab_client.project.mergerequests.list(
            state='merged',
            source_branch=delivery_branch,
            order_by='updated_at', 
            sort='desc',
            get_all=True
        )
        
        # 根据实际情况选择合适的方案
        # 通常交付分支是target_branch，包含多个feature分支的合并
        return target_branch_mrs
    
    def generate_report(self, results):
        """生成验证报告"""
        
        print("\n" + "="*80)
        print("📊 交付分支MR验证报告")
        print("="*80)
        
        total_repos = len(results)
        total_mrs = sum(r['total_mrs'] for r in results.values())
        total_merged = sum(r['merged_count'] for r in results.values())
        total_not_merged = sum(r['not_merged_count'] for r in results.values())
        
        print(f"📋 验证概览:")
        print(f"  • 验证仓库数: {total_repos}")
        print(f"  • 总MR数量: {total_mrs}")
        print(f"  • 已进入主线: {total_merged}")
        print(f"  • 未进入主线: {total_not_merged}")
        print(f"  • 进入率: {total_merged/total_mrs*100:.1f}%" if total_mrs > 0 else "  • 进入率: N/A")
        
        print(f"\n📊 分仓库详情:")
        for repo_name, result in results.items():
            print(f"\n🏢 {repo_name}:")
            print(f"  交付分支: {result['delivery_branch']}")
            print(f"  主线分支: {result['master_branch']}")
            print(f"  MR总数: {result['total_mrs']}")
            print(f"  已合并: {result['merged_count']}")
            print(f"  未合并: {result['not_merged_count']}")
            print(f"  无变更: {result['no_changes_count']}")
            
            # 显示未合并的MR
            not_merged = [r for r in result['results'] if r['status'] == 'NOT_MERGED']
            if not_merged:
                print(f"  ⚠️ 未进入主线的MR:")
                for mr in not_merged[:5]:  # 显示前5个
                    print(f"    • MR #{mr['mr_id']}: {mr['title'][:40]}...")
                if len(not_merged) > 5:
                    print(f"    ... 还有 {len(not_merged) - 5} 个")


def main():
    """主函数 - 使用示例"""
    
    # 配置示例
    config = {
        "repositories": [
            {
                "name": "DTU项目",
                "gitlab_url": "https://code.deeproute.ai",
                "gitlab_token": "your-token",
                "project_id": 1752,
                "repo_path": "/home/majiahui/codetree/repo/dtu",
                "delivery_branch": "Release_Thoru_Share_From_Daily_250829",  # 实际的交付分支
                "master_branch": "dev_master",
                "search_days": 60
            }
        ]
    }
    
    # 创建验证器
    validator = DeliveryBranchMRValidator(config)
    
    # 执行验证
    results = validator.validate_all_repositories()
    
    # 生成报告
    validator.generate_report(results)


if __name__ == '__main__':
    main()

"""
结果输出器模块
负责格式化输出验证结果
"""

import json
from typing import List, Dict, Any


class ResultOutputer:
    """结果输出器"""

    def __init__(self):
        """初始化输出器"""
        pass

    def output_results(self, validated_results: List[Dict[str, Any]], output_format: str = 'console') -> str:
        """
        输出验证结果

        Args:
            validated_results: 验证结果列表
            output_format: 输出格式 ('console', 'json', 'markdown')

        Returns:
            格式化的输出字符串（JSON和Markdown格式时返回）
        """
        if output_format == 'console':
            self._output_to_console(validated_results)
            return ""
        elif output_format == 'json':
            return self._output_to_json(validated_results)
        elif output_format == 'markdown':
            return self._output_to_markdown(validated_results)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")

    def _output_to_console(self, results: List[Dict[str, Any]]) -> None:
        """
        控制台输出

        Args:
            results: 验证结果列表
        """
        print("\n" + "="*80)
        print("MR 回流验证结果")
        print("="*80)

        # 统计信息
        total = len(results)
        entered = sum(1 for r in results if r['conclusion'] == '已进入主线')
        suspected = sum(1 for r in results if r['conclusion'] == '疑似已进入')
        not_entered = sum(1 for r in results if r['conclusion'] == '未进入主线')

        print("\n📊 统计信息:")
        print(f"  总数: {total}")
        print(f"  已进入主线: {entered}")
        print(f"  疑似已进入: {suspected}")
        print(f"  未进入主线: {not_entered}")
        print("-" * 80)

        for result in results:
            print(f"\n🔍 MR #{result['mr_id']} - {result['file_path']}")
            print(f"📋 状态: {result['conclusion']}")
            print(f"💡 原因: {result['reason']}")
            print(f"🎯 建议: {result['recommendation']}")

            if result['matched']:
                print(f"🔗 匹配提交: {result['match_commit'][:8]}")
                print(f"📈 置信度: {result['confidence']:.2f}")

            print("-" * 40)

        # 输出建议
        self._print_recommendations(results)

    def _print_recommendations(self, results: List[Dict[str, Any]]) -> None:
        """输出总体建议"""
        not_entered = [r for r in results if r['conclusion'] == '未进入主线']
        suspected = [r for r in results if r['conclusion'] == '疑似已进入']

        if not_entered:
            print("\n⚠️  需要处理的MR:")
            for result in not_entered:
                print(f"  • MR #{result['mr_id']}: {result['file_path']}")

        if suspected:
            print("\n🤔  建议人工确认的MR:")
            for result in suspected:
                print(f"  • MR #{result['mr_id']}: {result['file_path']}")

    def _output_to_json(self, results: List[Dict[str, Any]]) -> str:
        """
        JSON格式输出

        Args:
            results: 验证结果列表

        Returns:
            JSON字符串
        """
        return json.dumps(results, indent=2, ensure_ascii=False)

    def _output_to_markdown(self, results: List[Dict[str, Any]]) -> str:
        """
        Markdown格式输出

        Args:
            results: 验证结果列表

        Returns:
            Markdown字符串
        """
        md = "# MR 回流验证报告\n\n"

        # 统计信息
        total = len(results)
        entered = sum(1 for r in results if r['conclusion'] == '已进入主线')
        suspected = sum(1 for r in results if r['conclusion'] == '疑似已进入')
        not_entered = sum(1 for r in results if r['conclusion'] == '未进入主线')

        md += "## 📊 统计信息\n\n"
        md += f"- **总数**: {total}\n"
        md += f"- **已进入主线**: {entered}\n"
        md += f"- **疑似已进入**: {suspected}\n"
        md += f"- **未进入主线**: {not_entered}\n\n"

        md += "## 📋 详细结果\n\n"
        md += "| MR ID | 文件路径 | 状态 | 原因 | 建议 |\n"
        md += "|-------|----------|------|------|------|\n"

        for result in results:
            md += f"| {result['mr_id']} | {result['file_path']} | {result['conclusion']} | {result['reason']} | {result['recommendation']} |\n"

        md += "\n## 🎯 处理建议\n\n"

        # 未进入主线的MR
        not_entered = [r for r in results if r['conclusion'] == '未进入主线']
        if not_entered:
            md += "### ⚠️ 需要处理的MR\n\n"
            for result in not_entered:
                md += f"- MR #{result['mr_id']}: `{result['file_path']}`\n"

        # 疑似已进入的MR
        suspected = [r for r in results if r['conclusion'] == '疑似已进入']
        if suspected:
            md += "\n### 🤔 建议人工确认的MR\n\n"
            for result in suspected:
                md += f"- MR #{result['mr_id']}: `{result['file_path']}`\n"

        return md

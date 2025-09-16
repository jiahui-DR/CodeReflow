"""
匹配验证器模块
负责验证搜索结果并生成最终结论
"""

from typing import List, Dict, Any


class MatchValidator:
    """匹配结果验证器"""

    def __init__(self, confidence_threshold: float = 0.8):
        """
        初始化验证器

        Args:
            confidence_threshold: 置信度阈值
        """
        self.confidence_threshold = confidence_threshold

    def validate_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证搜索结果并生成最终结论

        Args:
            search_results: 搜索结果列表

        Returns:
            验证结果列表
        """
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

    def _determine_conclusion(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        根据匹配结果确定结论

        Args:
            result: 匹配结果

        Returns:
            结论字典
        """
        if result['matched'] and result['confidence'] >= self.confidence_threshold:
            if result.get('match_type') == 'direct_match':
                return {
                    'status': '已进入主线',
                    'reason': f'通过直接匹配确认已进入主线分支，匹配提交: {result["match_commit"][:8]}',
                    'recommendation': '无需操作'
                }
            else:
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

"""
指纹工具函数测试
"""

import unittest
from core_reflow.utils.fingerprint_utils import (
    extract_meaningful_lines,
    generate_content_fingerprint,
    generate_fingerprint_for_change,
    compare_fingerprints,
    calculate_similarity
)


class TestFingerprintUtils(unittest.TestCase):
    """指纹工具函数测试类"""

    def test_extract_meaningful_lines(self):
        """测试提取有意义的变更行"""
        diff_content = '''@@ -1,3 +1,5 @@
 def hello():
-    print("world")
+    print("hello world")
+    return True
'''
        lines = extract_meaningful_lines(diff_content)
        # 应该提取 print("world")(删除), print("hello world")(新增), return True(新增)
        self.assertEqual(len(lines), 3)
        self.assertIn('print("hello world")', lines)
        self.assertIn('return True', lines)
        self.assertIn('print("world")', lines)

    def test_extract_meaningful_lines_with_ignore_patterns(self):
        """测试忽略模式"""
        diff_content = '''@@ -1,5 +1,7 @@
+# This is a comment
+import os
 def hello():
-    print("world")
+    print("hello world")
+    return True
'''
        lines = extract_meaningful_lines(diff_content)
        # 注释和import语句应该被忽略，只有print语句的变更会被保留
        self.assertEqual(len(lines), 3)  # print("world"), print("hello world"), return True
        self.assertNotIn('# This is a comment', lines)
        self.assertNotIn('import os', lines)
        self.assertIn('print("hello world")', lines)
        self.assertIn('return True', lines)

    def test_generate_content_fingerprint(self):
        """测试内容指纹生成"""
        lines = ['print("hello")', 'return True']
        fingerprint = generate_content_fingerprint(lines)
        
        self.assertEqual(len(fingerprint), 16)
        self.assertIsInstance(fingerprint, str)
        
        # 相同内容应该生成相同指纹
        fingerprint2 = generate_content_fingerprint(lines)
        self.assertEqual(fingerprint, fingerprint2)
        
        # 不同内容应该生成不同指纹
        different_lines = ['print("world")', 'return False']
        fingerprint3 = generate_content_fingerprint(different_lines)
        self.assertNotEqual(fingerprint, fingerprint3)

    def test_generate_fingerprint_for_change(self):
        """测试变更指纹生成"""
        change = {
            'file_path': 'test.py',
            'change_type': 'MODIFY',
            'diff_content': '''@@ -1,2 +1,3 @@
 def test():
-    pass
+    print("test")
+    return True
'''
        }
        
        fingerprint = generate_fingerprint_for_change(change, mr_id=123)
        
        self.assertIsNotNone(fingerprint)
        self.assertEqual(fingerprint['mr_id'], 123)
        self.assertEqual(fingerprint['file_path'], 'test.py')
        self.assertEqual(fingerprint['change_type'], 'MODIFY')
        self.assertEqual(len(fingerprint['fingerprint']), 16)

    def test_generate_fingerprint_for_empty_change(self):
        """测试空变更的指纹生成"""
        change = {
            'file_path': 'test.py',
            'change_type': 'MODIFY',
            'diff_content': '''@@ -1,1 +1,1 @@
 # No meaningful changes
'''
        }
        
        fingerprint = generate_fingerprint_for_change(change)
        self.assertIsNone(fingerprint)  # 空变更应该返回None

    def test_compare_fingerprints(self):
        """测试指纹比较"""
        fp1 = "abc123def456"
        fp2 = "abc123def456"
        fp3 = "xyz789uvw012"
        
        self.assertTrue(compare_fingerprints(fp1, fp2))
        self.assertFalse(compare_fingerprints(fp1, fp3))

    def test_calculate_similarity(self):
        """测试相似度计算"""
        lines1 = ['print("hello")', 'return True', 'x = 1']
        lines2 = ['print("hello")', 'return False', 'y = 2']
        
        similarity = calculate_similarity(lines1, lines2)
        self.assertGreater(similarity, 0)
        self.assertLess(similarity, 1)
        
        # 完全相同的行
        similarity_same = calculate_similarity(lines1, lines1)
        self.assertEqual(similarity_same, 1.0)
        
        # 完全不同的行
        lines3 = ['completely', 'different', 'code']
        similarity_diff = calculate_similarity(lines1, lines3)
        self.assertEqual(similarity_diff, 0.0)


if __name__ == '__main__':
    unittest.main()

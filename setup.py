#!/usr/bin/env python3
"""
Core Reflow - MR回流验证系统安装脚本
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README 文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取 requirements.txt
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="core-reflow",
    version="2.0.0",
    author="Core Reflow Team",
    author_email="core-reflow@example.com",
    description="MR回流验证系统 - 验证GitLab MR是否已进入主线分支",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/core-reflow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "core-reflow=core_reflow.main:main",
            "core-reflow-cli=core_reflow.cli:main",
        ],
    },
    package_data={
        "core_reflow": [
            "*.json",
            "config/*.json",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="git gitlab mr merge-request validation reflow",
    project_urls={
        "Bug Reports": "https://github.com/example/core-reflow/issues",
        "Source": "https://github.com/example/core-reflow",
        "Documentation": "https://github.com/example/core-reflow/docs",
    },
)

#!/usr/bin/env python3
"""
Setup script for TXT to EPUB Converter
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="txt-to-epub-converter",
    version="0.1.1",
    author="AI Development Team",
    author_email="",
    description="An intelligent tool for converting TXT files to EPUB format with smart chapter detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/txt-to-epub",
    py_modules=["webui"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "txt-to-epub=webui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.bat", "*.sh"],
    },
    keywords="txt epub converter ebook chapter detection gradio web-ui",
    project_urls={
        "Bug Reports": "https://github.com/your-username/txt-to-epub/issues",
        "Source": "https://github.com/your-username/txt-to-epub",
        "Documentation": "https://github.com/your-username/txt-to-epub#readme",
    },
) 
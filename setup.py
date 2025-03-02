#!/usr/bin/env python3
"""
Setup script for the News Aggregator package.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read the requirements
with open("requirements.txt", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Package metadata
setup(
    name="news-aggregator",
    version="1.0.0",
    description="A comprehensive news aggregation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/news-aggregator",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "news-api=api.main:run_api",
            "news-crawler=crawler.main:run_crawler",
            "news-processor=processor.main:run_processor",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="news, aggregator, crawler, api, web",
    project_urls={
        "Documentation": "https://github.com/yourusername/news-aggregator",
        "Source": "https://github.com/yourusername/news-aggregator",
        "Tracker": "https://github.com/yourusername/news-aggregator/issues",
    },
)
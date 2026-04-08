"""
Setup script for Production Incident Response Simulator.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="production-incident-simulator",
    version="1.0.0",
    author="Senior Distributed Systems Engineer",
    description="OpenEnv-compatible RL environment for production incident response",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/incident-simulator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "python-dotenv>=1.0.0",
        ],
    },
)

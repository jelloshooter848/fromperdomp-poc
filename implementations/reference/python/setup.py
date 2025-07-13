from setuptools import setup, find_packages

setup(
    name="domp",
    version="0.1.0",
    description="Reference implementation of the Decentralized Online Marketplace Protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DOMP Protocol Contributors",
    url="https://github.com/domp-protocol/domp",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "secp256k1>=0.14.0",
        "websockets>=10.0",
        "aiohttp>=3.8.0",
        "cryptography>=3.4.0",
        "jsonschema>=4.0.0",
        "click>=8.0.0",
        "pydantic>=1.10.0",
    ],
    extras_require={
        "lightning": [
            "lnd-grpc-client>=0.3.0",
            "grpcio>=1.50.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "mypy>=1.0.0",
            "flake8>=5.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "domp=domp.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
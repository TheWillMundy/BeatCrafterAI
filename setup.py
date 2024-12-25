from setuptools import setup, find_packages

setup(
    name="ai-beat-saber",
    version="0.1.0",
    description="AI-powered Beat Saber map generator and analyzer",
    author="Will Mundy",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.2",
        "librosa>=0.10.1",
        "numpy>=1.26.2",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "tqdm>=4.66.1",
        "ffmpeg-python>=0.2.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 
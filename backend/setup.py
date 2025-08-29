from setuptools import setup, find_packages

setup(
    name="word-addin-mcp-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic-settings",
        "python-dotenv",
        "requests",
        "beautifulsoup4",
        "aiohttp",
        "structlog",
        "openai",
        "langchain",
        "langchain-openai",
    ],
    python_requires=">=3.9",
)

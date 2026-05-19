# setup.py
from setuptools import setup, find_packages

setup(
    name="zoom-manager",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        'python-dotenv>=1.2.2,<2',
        'requests>=2.34.2,<3',
        'pytz>=2026.2',
        'tqdm>=4.67.3,<5'
    ],
)

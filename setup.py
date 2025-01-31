# setup.py
from setuptools import setup, find_packages

setup(
    name="zoom-manager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        'requests',
        'google-auth',
        'google-auth-oauthlib',
        'google-auth-httplib2',
        'google-api-python-client',
        'tqdm',
        'pytz'
    ],
)
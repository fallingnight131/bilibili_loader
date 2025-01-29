from setuptools import setup, find_packages

setup(
    name='bilibili_loader',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'moviepy',
        'streamlit',
    ],
    entry_points={
        'console_scripts': [
            'bilibili_loader=bilibili_loader.main:main',
        ],
    },
)
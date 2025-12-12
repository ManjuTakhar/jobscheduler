"""Setup script for the job scheduler package."""
from setuptools import setup, find_packages

setup(
    name='job-scheduler',
    version='1.0.0',
    description='A lightweight, in-memory job scheduling service',
    packages=find_packages(),
    install_requires=[
        'croniter>=2.0.0',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'job-scheduler=job_scheduler.main:main',
        ],
    },
)


from setuptools import setup, find_packages

setup(
    name="transportation-optimization",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pandas>=1.3.0',
        'pulp>=2.7.0',
        'streamlit>=1.31.0',
        'seaborn>=0.11.0',
        'matplotlib>=3.3.0',
        'numpy>=1.19.0',
        'openpyxl>=3.0.0',
    ],
    python_requires='>=3.7',
    author="Your Name",
    author_email="your.email@example.com",
    description="A transportation optimization system using MILP",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Data-Science-PIHC/Transportation-Optimization-MILP",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

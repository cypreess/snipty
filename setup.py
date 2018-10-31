from setuptools import setup
from snipty import __VERSION__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="snipty",
    version=__VERSION__,
    packages=["snipty"],
    python_requires=">3.6",
    url="https://github.com/cypreess/snipty",
    license="MIT",
    author="Kris Dorosz",
    author_email="cypreess@gmail.com",
    description="Track snippets use in your codebase with ease",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["requests>=2.18", "termcolor>=1.1.0", "PyYAML>=3.13"],
    scripts=["bin/snipty"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

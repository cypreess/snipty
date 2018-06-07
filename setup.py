from setuptools import setup
from snipty import __VERSION__

setup(
    name='snipty',
    version=__VERSION__,
    packages=['snipty'],
    python_requires='>3.6',
    url='https://github.com/cypreess/snipty',
    license='MIT',
    author='Kris Dorosz',
    author_email='cypreess@gmail.com',
    description='Minimalistic package manager for snippets.',
    install_requires=['requests>=2.18', 'termcolor>=1.1.0'],
    scripts=['bin/snipty']
)

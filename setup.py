from setuptools import setup, find_packages

setup(name='python_mitmocker',
    version='0.0.1',
    description='MITM proxy mock server',
    author='pykaso',
    url='https://github.com/pykaso/mitmocker',
    packages=['mitmocker'],
    install_requires=['mitmproxy']
)
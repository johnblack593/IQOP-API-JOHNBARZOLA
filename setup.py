"""The python wrapper for IQ Option API package setup."""
from setuptools import (setup, find_packages)
from iqoptionapi import __version__

setup(
    name="iqoptionapi",
    version=__version__,
    packages=find_packages(),
    install_requires=["flake8>=7.0.0", "black>=24.2.0", "requests>=2.31.0", "certifi>=2024.2.2", "websocket-client>=1.8.0"],
    include_package_data=True,
    description="IQ Option API JCBV Wrapper (Modernized Asynchronous Edition)",
    long_description="IQ Option API JCBV Wrapper (Modernized Asynchronous Edition)",
    url="https://github.com/johnblack593/IQOption-API-JCBV",
    author="JCBV Developer / JCBV",
    zip_safe=False
)

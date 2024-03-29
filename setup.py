from setuptools import find_namespace_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="alleycat-reactive",
    version="0.4.8",
    author="Xavier Cho",
    author_email="mysticfallband@gmail.com",
    description="A simple Python library to provide an API to implement the Reactive Object Pattern (ROP).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mysticfall/alleycat-reactive",
    packages=find_namespace_packages(include=["alleycat.*"]),
    install_requires=["returns==0.17.0", "rx==3.2.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

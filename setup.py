import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="alleycat-reactive",
    version="0.1",
    author="Xavier Cho",
    author_email="mysticfallband@gmail.com",
    description="A simple Python library to provide an API to implement the Reactive Object Pattern (ROP).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mysticfall/alleycat-reactive",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

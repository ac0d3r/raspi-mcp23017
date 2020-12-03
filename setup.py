from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="raspi_mcp23017",
    version="0.0.1",
    description="RaspberryPi mcp23017 I/O expansion board",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="@buzz",
    url="https://github.com/Buzz2d0/raspi-mcp23017",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        'smbus2',
    ]
)

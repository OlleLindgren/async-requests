import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="async-requests",
    version="v0.1.2",
    author="Olle Lindgren",
    author_email="lindgrenolle@live.se",
    description="A package for easily making asyncronous GET requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OlleLindgren/async-requests",
    packages=setuptools.find_packages(),
    install_requires=[
          'asyncio',
          'aiohttp'
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
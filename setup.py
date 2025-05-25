from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name="fitler",
    version="0.0.1",
    description="A Python package for keeping multiple fitness services in sync, or just using them",
    long_description=(here / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Chris Kelly",
    author_email="ckdake@ckdake.com", 
    url="https://github.com/ckdake/fitler", 
    license="CC BY-NC 4.0",
    packages=["fitler"],
    install_requires=[],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
        "Development Status :: 3 - Alpha",
    ],
    include_package_data=True,
)

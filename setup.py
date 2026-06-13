from pathlib import Path
from setuptools import setup, find_packages


def get_version():
    """Read version from __version__.py at package root."""
    version_file = Path(__file__).parent / "__version__.py"
    namespace = {}
    with open(version_file) as f:
        exec(f.read(), namespace)
    return namespace["__version__"]


def get_long_description():
    readme_file = Path(__file__).parent / "Readme.md"
    if readme_file.exists():
        with open(readme_file, encoding="utf-8") as f:
            return f.read()
    return "AcoustiCAD — Professional audio system design tool"


setup(
    name="acousticad",
    version=get_version(),
    author="Free Forge Labs",
    author_email="support@freeforgelabs.com",
    description="Professional audio system design tool for commercial and residential venues",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/FreeForgeLabs/AcoustiCAD",
    packages=find_packages(exclude=["venv*", "tests*", ".idea*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=5.15.0",
        "PySide6-sip>=12.0.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "pdf": ["PyMuPDF>=1.20.0"],
        "dev": ["pytest>=6.0.0", "pytest-qt>=4.0.0", "PySide6-stubs"],
    },
    entry_points={
        "gui_scripts": [
            "acousticad=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json", "ui/resources/*"],
    },
    zip_safe=False,
)
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bin2dicom",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to convert binary medical imaging data to DICOM format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bin2dicom",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
            "pylint>=2.0",
            "ipykernel>=6.0",
            "jupyter>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bin2dicom=bin2dicom.cli:main",
        ],
    },
)

# Use the official Python 3.11 image as base
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system dependencies that might be needed for medical imaging libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create workspace directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    black \
    pytest \
    pytest-cov \
    ipykernel \
    jupyter \
    flake8 \
    pylint

# Set up Jupyter kernel
RUN python -m ipykernel install --user --name bin2dicom --display-name "bin2dicom Python"

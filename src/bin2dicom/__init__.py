"""
bin2dicom: A tool to convert binary medical imaging data to DICOM format.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .converter import BinaryToDicomConverter
from .reader import BinaryImageReader

__all__ = ["BinaryToDicomConverter", "BinaryImageReader"]

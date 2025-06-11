"""
bin2dicom: A tool to convert binary medical imaging data to DICOM format.
"""

__version__ = "0.1.0"
__author__ = "Constantina Giapintzaki"
__email__ = "costagiap@gmail.com"

from .converter import BinaryToDicomConverter
from .reader import BinaryImageReader

__all__ = ["BinaryToDicomConverter", "BinaryImageReader"]

"""
bin2dicom: A tool to convert binary medical imaging data to DICOM format.
"""

__version__ = "0.1.0"
__author__ = "Constantina Giapintzaki"
__email__ = "costagiap@gmail.com"

from .reader import BinaryImageReader
from .roi_parser import ROIParser
from .dose_parser import DosePlanParser
from .converter import BinaryToDicomConverter

__all__ = [
    "BinaryToDicomConverter",
    "BinaryImageReader",
    "ROIParser",
    "DosePlanParser"
]

__all__ = ["BinaryToDicomConverter", "BinaryImageReader"]

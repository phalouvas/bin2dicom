"""
Binary image reader for medical imaging data.
"""

import numpy as np
import struct
from typing import Dict, Any, Tuple
from pathlib import Path


class BinaryImageReader:
    """
    Reader for binary medical imaging data with associated header files.
    """

    def __init__(self, header_file: str):
        """
        Initialize the reader with a header file.

        Args:
            header_file: Path to the header file
        """
        self.header_file = Path(header_file)
        self.header_data = self._parse_header()

    def _parse_header(self) -> Dict[str, Any]:
        """Parse the header file to extract image parameters."""
        header_data = {}

        with open(self.header_file, 'r') as f:
            content = f.read()

        # Parse header parameters
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('//'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(';')

                    # Try to convert to appropriate type
                    if value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            header_data[key] = float(value)
                        else:
                            header_data[key] = int(value)
                    elif value.startswith('"') and value.endswith('"'):
                        header_data[key] = value[1:-1]
                    elif value.startswith(':'):
                        header_data[key] = value[1:].strip()
                    else:
                        header_data[key] = value

        return header_data

    def read_binary_image(self, image_file: str = None) -> np.ndarray:
        """
        Read the binary image data.

        Args:
            image_file: Path to the image file. If None, uses header file name with .img extension

        Returns:
            3D numpy array containing the image data
        """
        if image_file is None:
            image_file = self.header_file.with_suffix('.img')
        else:
            image_file = Path(image_file)

        # Get image dimensions from header
        x_dim = self.header_data.get('x_dim', 512)
        y_dim = self.header_data.get('y_dim', 512)
        z_dim = self.header_data.get('z_dim', 1)
        datatype = self.header_data.get('datatype', 1)
        bytes_pix = self.header_data.get('bytes_pix', 2)

        # Determine data type
        if datatype == 1 and bytes_pix == 2:
            dtype = np.int16
        elif datatype == 1 and bytes_pix == 1:
            dtype = np.int8
        elif datatype == 2:
            dtype = np.float32
        else:
            dtype = np.int16  # default

        # Read binary data
        with open(image_file, 'rb') as f:
            data = f.read()

        # Convert to numpy array
        total_voxels = x_dim * y_dim * z_dim
        image_array = np.frombuffer(data, dtype=dtype, count=total_voxels)

        # Reshape to 3D array (z, y, x) - standard medical imaging convention
        image_array = image_array.reshape((z_dim, y_dim, x_dim))

        return image_array

    def get_image_info(self) -> Dict[str, Any]:
        """Get comprehensive image information from header."""
        return {
            'dimensions': (
                self.header_data.get('x_dim', 512),
                self.header_data.get('y_dim', 512),
                self.header_data.get('z_dim', 1)
            ),
            'pixel_spacing': (
                self.header_data.get('x_pixdim', 1.0),
                self.header_data.get('y_pixdim', 1.0),
                self.header_data.get('z_pixdim', 1.0)
            ),
            'origin': (
                self.header_data.get('x_start', 0.0),
                self.header_data.get('y_start', 0.0),
                self.header_data.get('z_start', 0.0)
            ),
            'patient_position': self.header_data.get('patient_position', 'HFS'),
            'modality': self.header_data.get('modality', 'CT'),
            'manufacturer': self.header_data.get('manufacturer', ''),
            'model': self.header_data.get('model', ''),
            'patient_name': self.header_data.get('db_name', ''),
            'patient_id': self.header_data.get('patient_id', ''),
            'study_id': self.header_data.get('study_id', ''),
            'exam_id': self.header_data.get('exam_id', ''),
            'scan_date': self.header_data.get('date', ''),
            'datatype': self.header_data.get('datatype', 1),
            'bytes_per_pixel': self.header_data.get('bytes_pix', 2)
        }

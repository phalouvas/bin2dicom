"""
ROI (Region of Interest) parser for Pinnacle Treatment Planning System files.
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Any
from pathlib import Path


class ROIParser:
    """
    Parser for Pinnacle .roi files to extract structure sets.
    """

    def __init__(self, roi_file: str):
        """
        Initialize the ROI parser.

        Args:
            roi_file: Path to the .roi file
        """
        self.roi_file = Path(roi_file)
        self.rois = self._parse_roi_file()

    def _parse_roi_file(self) -> List[Dict[str, Any]]:
        """Parse the ROI file to extract all structures."""
        rois = []

        with open(self.roi_file, 'r') as f:
            content = f.read()

        # Split into individual ROI sections
        roi_sections = re.split(
            r'//-----------------------------------------------------\s*//\s*Beginning of ROI:', content)[1:]

        for section in roi_sections:
            roi_data = self._parse_roi_section(section)
            if roi_data:
                rois.append(roi_data)

        return rois

    def _parse_roi_section(self, section: str) -> Dict[str, Any]:
        """Parse an individual ROI section."""
        roi_data = {}

        # Extract ROI name from the first line
        lines = section.split('\n')
        if lines:
            name_match = re.search(r'^(.+?)\s*//-----', lines[0])
            if name_match:
                roi_data['name'] = name_match.group(1).strip()

        # Find the roi={ ... }; block
        roi_match = re.search(
            r'roi=\s*\{(.*?)\};\s*//\s*End of roi', section, re.DOTALL)
        if roi_match:
            roi_block = roi_match.group(1)
            roi_data.update(self._parse_roi_properties(roi_block))

        # Extract curves (contours)
        roi_data['contours'] = self._extract_contours(section)

        return roi_data

    def _parse_roi_properties(self, roi_block: str) -> Dict[str, Any]:
        """Parse properties within an ROI block."""
        properties = {}

        lines = roi_block.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('//'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(';')

                    # Convert to appropriate type
                    if value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            properties[key] = float(value)
                        else:
                            properties[key] = int(value)
                    else:
                        properties[key] = value
            elif '=' in line and not line.startswith('//'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(';')

                    # Convert to appropriate type
                    if value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            properties[key] = float(value)
                        else:
                            properties[key] = int(value)
                    else:
                        properties[key] = value

        return properties

    def _extract_contours(self, section: str) -> List[Dict[str, Any]]:
        """Extract contour data from ROI section."""
        contours = []

        # Find all curve blocks
        curve_pattern = r'curve\s*=\s*\{(.*?)\};\s*//\s*End of curve'
        curve_matches = re.finditer(curve_pattern, section, re.DOTALL)

        for match in curve_matches:
            curve_block = match.group(1)
            contour = self._parse_curve_block(curve_block)
            if contour:
                contours.append(contour)

        return contours

    def _parse_curve_block(self, curve_block: str) -> Dict[str, Any]:
        """Parse a single curve (contour) block."""
        contour = {}

        # Extract basic properties
        lines = curve_block.split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('//') and 'points' not in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(';')

                    if value.replace('.', '').replace('-', '').isdigit():
                        if '.' in value:
                            contour[key] = float(value)
                        else:
                            contour[key] = int(value)
                    else:
                        contour[key] = value

        # Extract points
        points_pattern = r'points\s*=\s*\{(.*?)\};'
        points_match = re.search(points_pattern, curve_block, re.DOTALL)

        if points_match:
            points_data = points_match.group(1)
            contour['points'] = self._parse_points(points_data)

        return contour

    def _parse_points(self, points_data: str) -> List[Tuple[float, float, float]]:
        """Parse contour points."""
        points = []

        # Extract coordinate triplets
        coord_pattern = r'(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)'
        coord_matches = re.finditer(coord_pattern, points_data)

        for match in coord_matches:
            x, y, z = map(float, match.groups())
            points.append((x, y, z))

        return points

    def get_structure_names(self) -> List[str]:
        """Get list of all structure names."""
        return [roi.get('name', f"ROI_{i}") for i, roi in enumerate(self.rois)]

    def get_structure_by_name(self, name: str) -> Dict[str, Any]:
        """Get structure data by name."""
        for roi in self.rois:
            if roi.get('name') == name:
                return roi
        return None

    def get_all_structures(self) -> List[Dict[str, Any]]:
        """Get all structure data."""
        return self.rois

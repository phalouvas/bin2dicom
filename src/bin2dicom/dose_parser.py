"""
Dose and plan parser for Pinnacle Treatment Planning System files.
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


class DosePlanParser:
    """
    Parser for Pinnacle .Trial files and associated dose data.
    """

    def __init__(self, trial_file: str, dose_data_dir: str = None):
        """
        Initialize the dose plan parser.

        Args:
            trial_file: Path to the .Trial file
            dose_data_dir: Directory containing binary dose files
        """
        self.trial_file = Path(trial_file)
        self.dose_data_dir = Path(
            dose_data_dir) if dose_data_dir else self.trial_file.parent
        self.trial_data = self._parse_trial_file()

    def _parse_trial_file(self) -> Dict[str, Any]:
        """Parse the trial file to extract plan parameters."""
        trial_data = {}

        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None

        for encoding in encodings:
            try:
                with open(self.trial_file, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError(
                f"Could not decode trial file {self.trial_file} with any standard encoding")

        # Parse the hierarchical structure
        trial_data = self._parse_block(content, 'Trial')

        return trial_data

    def _parse_block(self, content: str, block_name: str = None) -> Dict[str, Any]:
        """Parse a hierarchical block structure."""
        data = {}

        # Remove comments
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('//'):
                lines.append(line)

        content = '\n'.join(lines)

        # Find blocks and simple assignments
        i = 0
        content_lines = content.split('\n')

        while i < len(content_lines):
            line = content_lines[i].strip()

            if '=' in line:
                # Check if it's a simple assignment or block start
                if line.endswith('{'):
                    # Block start
                    key = line.split('=')[0].strip()
                    # Find matching closing brace
                    brace_count = 1
                    block_content = []
                    i += 1

                    while i < len(content_lines) and brace_count > 0:
                        current_line = content_lines[i]
                        if '{' in current_line:
                            brace_count += current_line.count('{')
                        if '}' in current_line:
                            brace_count -= current_line.count('}')

                        if brace_count > 0:
                            block_content.append(current_line)
                        i += 1

                    # Recursively parse the block
                    block_str = '\n'.join(block_content)
                    if key in data:
                        if not isinstance(data[key], list):
                            data[key] = [data[key]]
                        data[key].append(self._parse_block(block_str))
                    else:
                        data[key] = self._parse_block(block_str)

                elif ';' in line:
                    # Simple assignment
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().rstrip(';')

                        # Handle dotted keys (like DoseGrid.VoxelSize.X)
                        if '.' in key:
                            keys = key.split('.')
                            current = data
                            for k in keys[:-1]:
                                if k not in current:
                                    current[k] = {}
                                current = current[k]
                            key = keys[-1]
                            current[key] = self._convert_value(value)
                        else:
                            data[key] = self._convert_value(value)
            i += 1

        return data

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        value = value.strip()

        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '').isdigit():
            if '.' in value or 'e' in value.lower():
                return float(value)
            else:
                return int(value)
        elif value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        else:
            return value

    def get_dose_grid_info(self) -> Dict[str, Any]:
        """Get dose grid information."""
        dose_grid = self.trial_data.get('DoseGrid', {})

        return {
            'voxel_size': (
                dose_grid.get('VoxelSize', {}).get('X', 0.3),
                dose_grid.get('VoxelSize', {}).get('Y', 0.3),
                dose_grid.get('VoxelSize', {}).get('Z', 0.3)
            ),
            'dimensions': (
                dose_grid.get('Dimension', {}).get('X', 1),
                dose_grid.get('Dimension', {}).get('Y', 1),
                dose_grid.get('Dimension', {}).get('Z', 1)
            ),
            'origin': (
                dose_grid.get('Origin', {}).get('X', 0.0),
                dose_grid.get('Origin', {}).get('Y', 0.0),
                dose_grid.get('Origin', {}).get('Z', 0.0)
            )
        }

    def get_prescription_info(self) -> Dict[str, Any]:
        """Get prescription information."""
        prescriptions = self.trial_data.get('PrescriptionList', {})
        if isinstance(prescriptions, dict) and 'Prescription' in prescriptions:
            prescription = prescriptions['Prescription']
            if isinstance(prescription, list):
                prescription = prescription[0]  # Take first prescription

            return {
                'name': prescription.get('Name', 'Prescription_1'),
                'dose': prescription.get('PrescriptionDose', 0),
                'fractions': prescription.get('NumberOfFractions', 1),
                'percent': prescription.get('PrescriptionPercent', 100),
                'method': prescription.get('Method', 'Prescribe'),
                'point': prescription.get('PrescriptionPoint', 'Isocenter')
            }
        return {}

    def get_beam_info(self) -> List[Dict[str, Any]]:
        """Get beam information."""
        beams = []

        # Look for beam data in the trial structure
        beam_list = self.trial_data.get('BeamList', {})
        if isinstance(beam_list, dict):
            for key, value in beam_list.items():
                if key.startswith('Beam') and isinstance(value, dict):
                    beam_info = {
                        'name': value.get('Name', key),
                        'energy': value.get('Energy', 6),
                        'gantry_angle': value.get('GantryAngle', 0),
                        'collimator_angle': value.get('CollimatorAngle', 0),
                        'couch_angle': value.get('CouchAngle', 0),
                        'monitor_units': value.get('MonitorUnits', 0),
                        'machine': value.get('Machine', {}).get('Name', 'Unknown')
                    }
                    beams.append(beam_info)

        return beams

    def read_dose_data(self, slice_index: int = None) -> Optional[np.ndarray]:
        """
        Read binary dose data files.

        Args:
            slice_index: Specific slice to read, or None for all slices

        Returns:
            3D dose array or None if files not found
        """
        dose_grid_info = self.get_dose_grid_info()
        dimensions = dose_grid_info['dimensions']

        if slice_index is not None:
            # Read specific slice
            dose_file = self.dose_data_dir / \
                f"{self.trial_file.stem}.binary.{slice_index:03d}"
            if dose_file.exists():
                with open(dose_file, 'rb') as f:
                    data = np.frombuffer(f.read(), dtype=np.float32)
                    return data.reshape(dimensions[1], dimensions[0])  # Y, X
            return None
        else:
            # Read all slices
            dose_array = np.zeros(
                dimensions[::-1], dtype=np.float32)  # Z, Y, X

            for z in range(dimensions[2]):
                dose_file = self.dose_data_dir / \
                    f"{self.trial_file.stem}.binary.{z:03d}"
                if dose_file.exists():
                    with open(dose_file, 'rb') as f:
                        data = np.frombuffer(f.read(), dtype=np.float32)
                        if len(data) == dimensions[0] * dimensions[1]:
                            dose_array[z] = data.reshape(
                                dimensions[1], dimensions[0])

            return dose_array

    def get_patient_info(self) -> Dict[str, Any]:
        """Get patient representation information."""
        patient_rep = self.trial_data.get('PatientRepresentation', {})

        return {
            'volume_name': patient_rep.get('PatientVolumeName', ''),
            'ct_to_density': patient_rep.get('CtToDensityName', ''),
            'ct_to_density_version': patient_rep.get('CtToDensityVersion', ''),
            'dm_table': patient_rep.get('DMTableName', ''),
            'dm_table_version': patient_rep.get('DMTableVersion', '')
        }

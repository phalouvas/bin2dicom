#!/usr/bin/env python3
"""
Simple usage example for bin2dicom converter.
"""

from bin2dicom import BinaryToDicomConverter
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def convert_example():
    """Simple example of converting medical imaging data to DICOM."""

    # Input file paths
    header_file = "data/ImageSet_0.header"
    roi_file = "data/plan.roi"
    trial_file = "data/plan.Trial"
    output_dir = "dicom_output"

    # Create converter
    converter = BinaryToDicomConverter(
        header_file=header_file,
        roi_file=roi_file,
        trial_file=trial_file
    )

    # Convert CT images
    print("Converting CT images...")
    ct_files = converter.convert_ct_images(output_dir)

    # Convert RT Structure Set
    print("Converting RT Structure Set...")
    converter.convert_rt_structure_set(output_dir, ct_files)

    # Convert RT Dose (if binary dose files exist)
    try:
        print("Converting RT Dose...")
        converter.convert_rt_dose(output_dir, ct_files)
    except Exception as e:
        print(f"RT Dose conversion skipped: {e}")

    # Convert RT Plan
    print("Converting RT Plan...")
    converter.convert_rt_plan(output_dir, ct_files)

    print(f"Conversion complete! Check the '{output_dir}' directory.")


if __name__ == "__main__":
    convert_example()

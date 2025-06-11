#!/usr/bin/env python3
"""
Demo script for bin2dicom converter.
This script demonstrates the complete conversion process from binary medical 
imaging data to DICOM format.
"""

from bin2dicom import BinaryToDicomConverter
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Run the complete conversion demo."""

    # Define file paths
    data_dir = Path("data")
    output_dir = Path("output")

    header_file = data_dir / "ImageSet_0.header"
    image_file = data_dir / "ImageSet_0.img"
    roi_file = data_dir / "plan.roi"
    trial_file = data_dir / "plan.Trial"

    # Check if input files exist
    missing_files = []
    for file_path, name in [
        (header_file, "header"),
        (image_file, "image"),
        (roi_file, "ROI"),
        (trial_file, "trial")
    ]:
        if not file_path.exists():
            missing_files.append(f"{name}: {file_path}")

    if missing_files:
        print("Missing input files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return 1

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("=== Binary to DICOM Converter Demo ===\n")

    try:
        # Initialize converter
        print("1. Initializing converter...")
        converter = BinaryToDicomConverter(
            header_file=str(header_file),
            roi_file=str(roi_file),
            trial_file=str(trial_file)
        )
        print("   ✓ Converter initialized successfully")

        # Display image information
        print("\n2. Image Information:")
        image_info = converter.reader.get_image_info()
        print(f"   - Dimensions: {image_info['dimensions']}")
        print(f"   - Pixel Spacing: {image_info['pixel_spacing']}")
        print(f"   - Origin: {image_info['origin']}")
        print(f"   - Patient: {image_info['patient_name']}")
        print(f"   - Modality: {image_info['modality']}")
        print(f"   - Manufacturer: {image_info['manufacturer']}")

        # Display ROI information
        if converter.roi_parser:
            print("\n3. ROI Information:")
            structures = converter.roi_parser.get_structure_names()
            print(f"   - Number of structures: {len(structures)}")
            for i, name in enumerate(structures[:5]):  # Show first 5
                print(f"   - {i+1}: {name}")
            if len(structures) > 5:
                print(f"   - ... and {len(structures) - 5} more")

        # Display dose/plan information
        if converter.dose_parser:
            print("\n4. Dose/Plan Information:")
            dose_grid = converter.dose_parser.get_dose_grid_info()
            prescription = converter.dose_parser.get_prescription_info()
            beams = converter.dose_parser.get_beam_info()

            print(f"   - Dose grid dimensions: {dose_grid['dimensions']}")
            print(f"   - Dose grid voxel size: {dose_grid['voxel_size']}")
            print(
                f"   - Prescription dose: {prescription.get('dose', 'N/A')} cGy")
            print(
                f"   - Number of fractions: {prescription.get('fractions', 'N/A')}")
            print(f"   - Number of beams: {len(beams)}")

        # Convert CT images
        print("\n5. Converting CT images...")
        ct_files = converter.convert_ct_images(
            output_dir=str(output_dir),
            image_file=str(image_file)
        )
        print(f"   ✓ Created {len(ct_files)} CT DICOM files")

        # Convert RT Structure Set
        print("\n6. Converting RT Structure Set...")
        rt_struct_file = converter.convert_rt_structure_set(
            output_dir=str(output_dir),
            ct_files=ct_files
        )
        print(f"   ✓ Created RT Structure Set: {Path(rt_struct_file).name}")

        # Convert RT Dose
        print("\n7. Converting RT Dose...")
        try:
            rt_dose_file = converter.convert_rt_dose(
                output_dir=str(output_dir),
                ct_files=ct_files
            )
            print(f"   ✓ Created RT Dose: {Path(rt_dose_file).name}")
        except Exception as e:
            print(f"   ⚠ RT Dose conversion failed: {str(e)}")
            print("   (This may be normal if binary dose files are not available)")

        # Convert RT Plan
        print("\n8. Converting RT Plan...")
        rt_plan_file = converter.convert_rt_plan(
            output_dir=str(output_dir),
            ct_files=ct_files
        )
        print(f"   ✓ Created RT Plan: {Path(rt_plan_file).name}")

        # Summary
        print("\n=== Conversion Summary ===")
        output_files = list(output_dir.glob("*.dcm"))
        print(f"Total DICOM files created: {len(output_files)}")
        print(f"Output directory: {output_dir.absolute()}")

        # List output files by type
        ct_files_count = len(
            [f for f in output_files if f.name.startswith("CT_")])
        rt_files = [f for f in output_files if f.name.startswith("RT_")]

        print(f"\nFile breakdown:")
        print(f"  - CT images: {ct_files_count}")
        for rt_file in rt_files:
            print(f"  - {rt_file.name}")

        print(f"\nConversion completed successfully! 🎉")

        # Display file sizes
        print(f"\nFile sizes:")
        total_size = 0
        for file_path in sorted(output_files):
            size = file_path.stat().st_size
            total_size += size
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"  {file_path.name}: {size_str}")

        if total_size > 1024 * 1024:
            total_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            total_str = f"{total_size / 1024:.1f} KB"
        print(f"  Total: {total_str}")

    except Exception as e:
        print(f"\n❌ Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

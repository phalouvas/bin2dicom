#!/usr/bin/env python3
"""
Command-line interface for bin2dicom converter.
"""

import argparse
import sys
from pathlib import Path

from bin2dicom.converter import BinaryToDicomConverter


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert binary medical imaging data to DICOM format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert CT images only
  python -m bin2dicom.cli --header data/ImageSet_0.header --output output/

  # Convert CT images and RT Structure Set
  python -m bin2dicom.cli --header data/ImageSet_0.header --roi data/plan.roi --output output/

  # Convert all (CT, RT Structure Set, RT Dose, RT Plan)
  python -m bin2dicom.cli --header data/ImageSet_0.header --roi data/plan.roi --trial data/plan.Trial --output output/
        """
    )

    parser.add_argument(
        '--header',
        type=str,
        required=True,
        help='Path to the binary image header file'
    )

    parser.add_argument(
        '--image',
        type=str,
        help='Path to the binary image file (optional, will use header path with .img extension if not provided)'
    )

    parser.add_argument(
        '--roi',
        type=str,
        help='Path to the ROI file for RT Structure Set conversion'
    )

    parser.add_argument(
        '--trial',
        type=str,
        help='Path to the trial file for RT Dose and RT Plan conversion'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for DICOM files'
    )

    parser.add_argument(
        '--ct-only',
        action='store_true',
        help='Convert CT images only, ignore ROI and trial files'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate input files
    header_file = Path(args.header)
    if not header_file.exists():
        print(f"Error: Header file not found: {args.header}", file=sys.stderr)
        return 1

    if args.image:
        image_file = Path(args.image)
        if not image_file.exists():
            print(
                f"Error: Image file not found: {args.image}", file=sys.stderr)
            return 1
    else:
        image_file = None

    if args.roi:
        roi_file = Path(args.roi)
        if not roi_file.exists():
            print(f"Error: ROI file not found: {args.roi}", file=sys.stderr)
            return 1
    else:
        roi_file = None

    if args.trial:
        trial_file = Path(args.trial)
        if not trial_file.exists():
            print(
                f"Error: Trial file not found: {args.trial}", file=sys.stderr)
            return 1
    else:
        trial_file = None

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize converter
        if args.verbose:
            print(f"Initializing converter with header: {args.header}")

        converter = BinaryToDicomConverter(
            header_file=str(header_file),
            roi_file=str(roi_file) if roi_file else None,
            trial_file=str(trial_file) if trial_file else None
        )

        # Convert CT images
        if args.verbose:
            print("Converting CT images...")

        ct_files = converter.convert_ct_images(
            output_dir=str(output_dir),
            image_file=str(image_file) if image_file else None
        )

        if args.ct_only:
            print(f"Successfully converted {len(ct_files)} CT DICOM files")
            return 0

        # Convert RT Structure Set
        if roi_file:
            if args.verbose:
                print("Converting RT Structure Set...")

            rt_struct_file = converter.convert_rt_structure_set(
                output_dir=str(output_dir),
                ct_files=ct_files
            )
            print(f"Created RT Structure Set: {rt_struct_file}")

        # Convert RT Dose and RT Plan
        if trial_file:
            if args.verbose:
                print("Converting RT Dose...")

            rt_dose_file = converter.convert_rt_dose(
                output_dir=str(output_dir),
                ct_files=ct_files
            )
            print(f"Created RT Dose: {rt_dose_file}")

            if args.verbose:
                print("Converting RT Plan...")

            rt_plan_file = converter.convert_rt_plan(
                output_dir=str(output_dir),
                ct_files=ct_files
            )
            print(f"Created RT Plan: {rt_plan_file}")

        print(
            f"Conversion completed successfully. Output directory: {output_dir}")

    except Exception as e:
        print(f"Error during conversion: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

# Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Basic Usage

### 1. Convert All Data Types (Recommended)
```bash
python -m bin2dicom.cli \
    --header data/ImageSet_0.header \
    --roi data/plan.roi \
    --trial data/plan.Trial \
    --output dicom_output/
```

### 2. Convert CT Images Only
```bash
python -m bin2dicom.cli \
    --header data/ImageSet_0.header \
    --output ct_output/ \
    --ct-only
```

### 3. Python API Usage
```python
from bin2dicom import BinaryToDicomConverter

# Initialize converter
converter = BinaryToDicomConverter(
    header_file="data/ImageSet_0.header",
    roi_file="data/plan.roi", 
    trial_file="data/plan.Trial"
)

# Convert everything
ct_files = converter.convert_ct_images("output/")
converter.convert_rt_structure_set("output/", ct_files)
converter.convert_rt_dose("output/", ct_files)  
converter.convert_rt_plan("output/", ct_files)
```

## Expected Input Files

Your data folder should contain:
- `ImageSet_0.header` - Image geometry and patient info
- `ImageSet_0.img` - Binary CT image data  
- `plan.roi` - Structure/ROI definitions
- `plan.Trial` - Treatment plan parameters
- `plan.Trial.binary.XXX` - Binary dose files (optional)

## Expected Output

The tool creates standard DICOM files:
- `CT_000.dcm` to `CT_XXX.dcm` - CT image series
- `RT_STRUCT.dcm` - RT Structure Set
- `RT_DOSE.dcm` - RT Dose distribution
- `RT_PLAN.dcm` - RT Treatment Plan

## Testing

Run the demo to test with sample data:
```bash
python demo.py
```

## Troubleshooting

- **Encoding errors**: Tool automatically tries multiple encodings
- **Missing files**: Use `--verbose` flag for detailed error info
- **Large datasets**: Tool is memory efficient for clinical data sizes
- **DICOM validation**: Output files are standard-compliant DICOM

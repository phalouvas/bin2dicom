# bin2dicom

A comprehensive Python tool for converting binary medical imaging data to DICOM format. This tool specifically handles Pinnacle Treatment Planning System data formats and converts them to standard DICOM files including CT images, RT Structure Sets, RT Dose, and RT Plans.

## Features

- **CT Image Conversion**: Convert binary image data with header files to DICOM CT images
- **RT Structure Set**: Convert ROI (Region of Interest) files to DICOM RT Structure Sets
- **RT Dose**: Convert dose calculation data to DICOM RT Dose objects
- **RT Plan**: Convert treatment plan data to DICOM RT Plan objects
- **Comprehensive Metadata**: Preserves patient information, study details, and geometric data
- **Command-line Interface**: Easy-to-use CLI for batch processing
- **Python API**: Programmatic access for integration into larger workflows

## Installation

### From Source

```bash
git clone <repository-url>
cd bin2dicom
pip install -r requirements.txt
pip install -e .
```

### Dependencies

- Python 3.7+
- pydicom >= 2.4.0
- numpy >= 1.21.0
- scipy >= 1.7.0
- pillow >= 8.3.0
- python-dateutil >= 2.8.0

## Quick Start

### Command Line Usage

```bash
# Convert CT images only
python -m bin2dicom.cli --header data/ImageSet_0.header --output output/

# Convert CT images and RT Structure Set
python -m bin2dicom.cli --header data/ImageSet_0.header --roi data/plan.roi --output output/

# Convert all components (CT, RT Structure Set, RT Dose, RT Plan)
python -m bin2dicom.cli --header data/ImageSet_0.header --roi data/plan.roi --trial data/plan.Trial --output output/
```

### Python API Usage

```python
from bin2dicom import BinaryToDicomConverter

# Initialize converter
converter = BinaryToDicomConverter(
    header_file="data/ImageSet_0.header",
    roi_file="data/plan.roi",
    trial_file="data/plan.Trial"
)

# Convert CT images
ct_files = converter.convert_ct_images("output/")

# Convert RT Structure Set
converter.convert_rt_structure_set("output/", ct_files)

# Convert RT Dose
converter.convert_rt_dose("output/", ct_files)

# Convert RT Plan
converter.convert_rt_plan("output/", ct_files)
```

## File Format Support

### Input Formats

- **Header Files** (`.header`): Contains image geometry, patient info, and acquisition parameters
- **Binary Image Files** (`.img`): Raw binary CT image data
- **ROI Files** (`.roi`): Pinnacle ROI/structure definitions
- **Trial Files** (`.Trial`): Pinnacle treatment plan and dose calculation parameters
- **Binary Dose Files** (`.binary.XXX`): Binary dose distribution data

### Output Formats

- **DICOM CT Images**: Standard DICOM CT image series
- **DICOM RT Structure Set**: DICOM-RT structure definitions
- **DICOM RT Dose**: DICOM-RT dose distributions
- **DICOM RT Plan**: DICOM-RT treatment plans

## Examples

### Run the Demo

```bash
python demo.py
```

This will process the sample data in the `data/` directory and create DICOM files in the `output/` directory.

### Simple Example

```bash
python example.py
```

A minimal example showing the basic conversion workflow.

## Data Structure

The tool expects the following file structure:

```
data/
├── ImageSet_0.header     # Image geometry and patient info
├── ImageSet_0.img        # Binary CT image data
├── plan.roi              # Structure/ROI definitions
├── plan.Trial            # Treatment plan parameters
├── plan.Trial.binary.000 # Dose data slice 0
├── plan.Trial.binary.001 # Dose data slice 1
└── ...                   # Additional dose slices
```

## Header File Format

The header file contains key-value pairs defining:

- Image dimensions (`x_dim`, `y_dim`, `z_dim`)
- Pixel spacing (`x_pixdim`, `y_pixdim`, `z_pixdim`)
- Image origin (`x_start`, `y_start`, `z_start`)
- Patient information (`db_name`, `patient_id`, `study_id`)
- Scanner details (`manufacturer`, `model`, `modality`)
- Data format (`datatype`, `bytes_pix`)

## API Reference

### BinaryToDicomConverter

Main converter class for binary to DICOM conversion.

```python
converter = BinaryToDicomConverter(header_file, roi_file=None, trial_file=None)
```

#### Methods

- `convert_ct_images(output_dir, image_file=None)`: Convert CT images
- `convert_rt_structure_set(output_dir, ct_files=None)`: Convert ROI to RT Structure Set
- `convert_rt_dose(output_dir, ct_files=None)`: Convert dose data to RT Dose
- `convert_rt_plan(output_dir, ct_files=None)`: Convert plan to RT Plan

### BinaryImageReader

Reads binary image data and header files.

```python
reader = BinaryImageReader(header_file)
image_array = reader.read_binary_image(image_file)
info = reader.get_image_info()
```

### ROIParser

Parses Pinnacle ROI files.

```python
parser = ROIParser(roi_file)
structures = parser.get_all_structures()
names = parser.get_structure_names()
```

### DosePlanParser

Parses Pinnacle trial and dose files.

```python
parser = DosePlanParser(trial_file)
dose_grid = parser.get_dose_grid_info()
prescription = parser.get_prescription_info()
dose_array = parser.read_dose_data()
```

## Error Handling

The tool includes comprehensive error handling for:

- Missing input files
- Corrupted or invalid data
- Unsupported file formats
- DICOM generation errors

Use the `--verbose` flag for detailed error information.

## Limitations

- Currently supports Pinnacle Treatment Planning System formats
- Binary dose files must follow the `.binary.XXX` naming convention
- Limited to axial image orientations
- Assumes standard coordinate systems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues, questions, or contributions, please [create an issue](link-to-issues) or contact the maintainers.

## Version History

- **0.1.0**: Initial release with basic CT, RT Structure Set, RT Dose, and RT Plan conversion
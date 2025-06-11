"""
Main converter class for binary medical imaging data to DICOM format.
"""

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import generate_uid, PYDICOM_ROOT_UID
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import tempfile
import os

from .reader import BinaryImageReader
from .roi_parser import ROIParser
from .dose_parser import DosePlanParser


class BinaryToDicomConverter:
    """
    Main converter class for converting binary medical imaging data to DICOM format.
    """

    def __init__(self, header_file: str, roi_file: str = None, trial_file: str = None):
        """
        Initialize the converter.

        Args:
            header_file: Path to the binary image header file
            roi_file: Path to the ROI file (optional)
            trial_file: Path to the trial file (optional)
        """
        self.reader = BinaryImageReader(header_file)
        self.roi_parser = ROIParser(roi_file) if roi_file else None
        self.dose_parser = DosePlanParser(trial_file) if trial_file else None

        # Generate UIDs for the study
        self.study_instance_uid = generate_uid()
        self.series_instance_uid = generate_uid()
        self.frame_of_reference_uid = generate_uid()

    def convert_ct_images(self, output_dir: str, image_file: str = None) -> List[str]:
        """
        Convert binary CT images to DICOM format.

        Args:
            output_dir: Output directory for DICOM files
            image_file: Path to binary image file (optional)

        Returns:
            List of created DICOM file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Read the binary image data
        image_array = self.reader.read_binary_image(image_file)
        image_info = self.reader.get_image_info()

        created_files = []

        # Create DICOM files for each slice
        for slice_idx in range(image_array.shape[0]):
            slice_data = image_array[slice_idx]

            # Create DICOM dataset
            ds = self._create_ct_dicom_dataset(
                slice_data, slice_idx, image_info)

            # Save DICOM file
            filename = f"CT_{slice_idx:03d}.dcm"
            filepath = output_path / filename
            ds.save_as(str(filepath))
            created_files.append(str(filepath))

        print(f"Created {len(created_files)} CT DICOM files in {output_dir}")
        return created_files

    def convert_rt_structure_set(self, output_dir: str, ct_files: List[str] = None) -> str:
        """
        Convert ROI data to DICOM RT Structure Set.

        Args:
            output_dir: Output directory for DICOM files
            ct_files: List of CT DICOM files for reference

        Returns:
            Path to created RT Structure Set file
        """
        if not self.roi_parser:
            raise ValueError("No ROI file provided during initialization")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create RT Structure Set DICOM dataset
        ds = self._create_rt_structure_set_dicom(ct_files)

        # Save DICOM file
        filename = "RT_STRUCT.dcm"
        filepath = output_path / filename
        ds.save_as(str(filepath))

        print(f"Created RT Structure Set DICOM file: {filepath}")
        return str(filepath)

    def convert_rt_dose(self, output_dir: str, ct_files: List[str] = None) -> str:
        """
        Convert dose data to DICOM RT Dose.

        Args:
            output_dir: Output directory for DICOM files
            ct_files: List of CT DICOM files for reference

        Returns:
            Path to created RT Dose file
        """
        if not self.dose_parser:
            raise ValueError("No trial file provided during initialization")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Read dose data
        dose_array = self.dose_parser.read_dose_data()
        if dose_array is None:
            raise ValueError("Could not read dose data")

        # Create RT Dose DICOM dataset
        ds = self._create_rt_dose_dicom(dose_array, ct_files)

        # Save DICOM file
        filename = "RT_DOSE.dcm"
        filepath = output_path / filename
        ds.save_as(str(filepath))

        print(f"Created RT Dose DICOM file: {filepath}")
        return str(filepath)

    def convert_rt_plan(self, output_dir: str, ct_files: List[str] = None) -> str:
        """
        Convert trial data to DICOM RT Plan.

        Args:
            output_dir: Output directory for DICOM files
            ct_files: List of CT DICOM files for reference

        Returns:
            Path to created RT Plan file
        """
        if not self.dose_parser:
            raise ValueError("No trial file provided during initialization")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create RT Plan DICOM dataset
        ds = self._create_rt_plan_dicom(ct_files)

        # Save DICOM file
        filename = "RT_PLAN.dcm"
        filepath = output_path / filename
        ds.save_as(str(filepath))

        print(f"Created RT Plan DICOM file: {filepath}")
        return str(filepath)

    def _create_ct_dicom_dataset(self, slice_data: np.ndarray, slice_idx: int, image_info: Dict[str, Any]) -> FileDataset:
        """Create a DICOM dataset for a CT slice."""

        # Create file meta information
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = PYDICOM_ROOT_UID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # Implicit VR Little Endian

        # Create main dataset
        ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)

        # Patient information
        ds.PatientName = image_info.get('patient_name', 'Anonymous')
        ds.PatientID = str(image_info.get('patient_id', '12345'))
        ds.PatientBirthDate = ''
        ds.PatientSex = ''

        # Study information
        ds.StudyInstanceUID = self.study_instance_uid
        ds.StudyID = str(image_info.get('study_id', '1'))
        ds.StudyDate = image_info.get(
            'scan_date', datetime.now().strftime('%Y%m%d'))
        ds.StudyTime = ''
        ds.AccessionNumber = str(image_info.get('exam_id', ''))

        # Series information
        ds.SeriesInstanceUID = self.series_instance_uid
        ds.SeriesNumber = "1"
        ds.SeriesDate = ds.StudyDate
        ds.SeriesTime = ''
        ds.Modality = image_info.get('modality', 'CT')
        ds.SeriesDescription = 'CT Images'

        # Instance information
        ds.SOPInstanceUID = generate_uid()
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = str(slice_idx + 1)

        # Image information
        ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = 'MONOCHROME2'
        ds.Rows = slice_data.shape[0]
        ds.Columns = slice_data.shape[1]
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1  # Signed

        # Spatial information
        pixel_spacing = image_info.get('pixel_spacing', (1.0, 1.0, 1.0))
        origin = image_info.get('origin', (0.0, 0.0, 0.0))

        # Row spacing, Column spacing
        ds.PixelSpacing = [pixel_spacing[1], pixel_spacing[0]]
        ds.SliceThickness = pixel_spacing[2]
        ds.SpacingBetweenSlices = pixel_spacing[2]

        # Calculate image position for this slice
        z_position = origin[2] + slice_idx * pixel_spacing[2]
        ds.ImagePositionPatient = [origin[0], origin[1], z_position]

        # Image orientation (standard axial)
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        # Frame of reference
        ds.FrameOfReferenceUID = self.frame_of_reference_uid
        ds.PositionReferenceIndicator = ''

        # Equipment information
        ds.Manufacturer = image_info.get('manufacturer', 'Unknown')
        ds.ManufacturerModelName = image_info.get('model', 'Unknown')
        ds.SoftwareVersions = 'bin2dicom 0.1.0'

        # Convert pixel data to appropriate format
        pixel_array = slice_data.astype(np.int16)
        ds.PixelData = pixel_array.tobytes()

        # Rescale information (if needed)
        ds.RescaleIntercept = "0"
        ds.RescaleSlope = "1"
        ds.RescaleType = 'HU'  # Hounsfield Units for CT

        return ds

    def _create_rt_structure_set_dicom(self, ct_files: List[str] = None) -> FileDataset:
        """Create a DICOM RT Structure Set dataset."""

        # Create file meta information
        file_meta = FileMetaDataset()
        # RT Structure Set Storage
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.3"
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = PYDICOM_ROOT_UID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"

        # Create main dataset
        ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)

        # Patient and study information
        image_info = self.reader.get_image_info()
        ds.PatientName = image_info.get('patient_name', 'Anonymous')
        ds.PatientID = str(image_info.get('patient_id', '12345'))
        ds.StudyInstanceUID = self.study_instance_uid
        ds.StudyID = str(image_info.get('study_id', '1'))
        ds.StudyDate = image_info.get(
            'scan_date', datetime.now().strftime('%Y%m%d'))

        # Series information
        ds.SeriesInstanceUID = generate_uid()
        ds.SeriesNumber = "2"
        ds.Modality = "RTSTRUCT"
        ds.SeriesDescription = "RT Structure Set"

        # Instance information
        ds.SOPInstanceUID = generate_uid()
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = "1"

        # RT Structure Set specific information
        ds.StructureSetLabel = "RT Structure Set"
        ds.StructureSetName = "RT Structure Set"
        ds.StructureSetDate = ds.StudyDate
        ds.StructureSetTime = datetime.now().strftime('%H%M%S')

        # Frame of reference
        ds.FrameOfReferenceUID = self.frame_of_reference_uid
        ds.PositionReferenceIndicator = ''

        # Referenced frame of reference
        ref_frame_seq = []
        ref_frame_item = Dataset()
        ref_frame_item.FrameOfReferenceUID = self.frame_of_reference_uid

        # RT referenced study
        rt_ref_study_seq = []
        rt_ref_study_item = Dataset()
        # Detached Study Management
        rt_ref_study_item.ReferencedSOPClassUID = "1.2.840.10008.3.1.2.3.1"
        rt_ref_study_item.ReferencedSOPInstanceUID = self.study_instance_uid

        # RT referenced series
        rt_ref_series_seq = []
        rt_ref_series_item = Dataset()
        rt_ref_series_item.SeriesInstanceUID = self.series_instance_uid

        # Contour image sequence (reference to CT images)
        contour_image_seq = []
        if ct_files:
            for ct_file in ct_files:
                try:
                    ct_ds = pydicom.dcmread(ct_file)
                    contour_image_item = Dataset()
                    contour_image_item.ReferencedSOPClassUID = ct_ds.SOPClassUID
                    contour_image_item.ReferencedSOPInstanceUID = ct_ds.SOPInstanceUID
                    contour_image_seq.append(contour_image_item)
                except:
                    pass

        rt_ref_series_item.ContourImageSequence = contour_image_seq
        rt_ref_series_seq.append(rt_ref_series_item)
        rt_ref_study_item.RTReferencedSeriesSequence = rt_ref_series_seq
        rt_ref_study_seq.append(rt_ref_study_item)
        ref_frame_item.RTReferencedStudySequence = rt_ref_study_seq
        ref_frame_seq.append(ref_frame_item)
        ds.ReferencedFrameOfReferenceSequence = ref_frame_seq

        # Structure set ROI sequence
        structures = self.roi_parser.get_all_structures()
        structure_set_roi_seq = []
        roi_contour_seq = []
        rt_roi_observations_seq = []

        for i, structure in enumerate(structures):
            roi_number = i + 1

            # Structure Set ROI
            structure_roi_item = Dataset()
            structure_roi_item.ROINumber = roi_number
            structure_roi_item.ReferencedFrameOfReferenceUID = self.frame_of_reference_uid
            structure_roi_item.ROIName = structure.get(
                'name', f'ROI_{roi_number}')
            structure_roi_item.ROIGenerationAlgorithm = 'MANUAL'
            structure_set_roi_seq.append(structure_roi_item)

            # ROI Contour
            roi_contour_item = Dataset()
            roi_contour_item.ReferencedROINumber = roi_number
            roi_contour_item.ROIDisplayColor = self._get_roi_color(
                structure.get('color', 'red'))

            # Contour sequence
            contour_seq = []
            for contour in structure.get('contours', []):
                if contour.get('points'):
                    contour_item = Dataset()
                    contour_item.ContourGeometricType = 'CLOSED_PLANAR'

                    # Convert points to DICOM format
                    points = contour['points']
                    contour_data = []
                    for point in points:
                        contour_data.extend([point[0], point[1], point[2]])

                    contour_item.NumberOfContourPoints = len(points)
                    contour_item.ContourData = contour_data

                    # Referenced image
                    contour_image_seq_item = []
                    # This would reference specific CT slices
                    contour_item.ContourImageSequence = contour_image_seq_item

                    contour_seq.append(contour_item)

            roi_contour_item.ContourSequence = contour_seq
            roi_contour_seq.append(roi_contour_item)

            # RT ROI Observations
            roi_obs_item = Dataset()
            roi_obs_item.ObservationNumber = roi_number
            roi_obs_item.ReferencedROINumber = roi_number
            roi_obs_item.ROIObservationLabel = structure.get(
                'name', f'ROI_{roi_number}')
            roi_obs_item.RTROIInterpretedType = 'ORGAN'
            roi_obs_item.ROIInterpreter = ''
            rt_roi_observations_seq.append(roi_obs_item)

        ds.StructureSetROISequence = structure_set_roi_seq
        ds.ROIContourSequence = roi_contour_seq
        ds.RTROIObservationsSequence = rt_roi_observations_seq

        return ds

    def _create_rt_dose_dicom(self, dose_array: np.ndarray, ct_files: List[str] = None) -> FileDataset:
        """Create a DICOM RT Dose dataset."""

        # Create file meta information
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.2"  # RT Dose Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = PYDICOM_ROOT_UID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"

        # Create main dataset
        ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)

        # Patient and study information
        image_info = self.reader.get_image_info()
        ds.PatientName = image_info.get('patient_name', 'Anonymous')
        ds.PatientID = str(image_info.get('patient_id', '12345'))
        ds.StudyInstanceUID = self.study_instance_uid
        ds.StudyID = str(image_info.get('study_id', '1'))
        ds.StudyDate = image_info.get(
            'scan_date', datetime.now().strftime('%Y%m%d'))

        # Series information
        ds.SeriesInstanceUID = generate_uid()
        ds.SeriesNumber = "3"
        ds.Modality = "RTDOSE"
        ds.SeriesDescription = "RT Dose"

        # Instance information
        ds.SOPInstanceUID = generate_uid()
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = "1"

        # Frame of reference
        ds.FrameOfReferenceUID = self.frame_of_reference_uid

        # Dose grid information
        dose_grid_info = self.dose_parser.get_dose_grid_info()

        # Image information
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = 'MONOCHROME2'
        ds.NumberOfFrames = dose_array.shape[0]
        ds.Rows = dose_array.shape[1]
        ds.Columns = dose_array.shape[2]
        ds.BitsAllocated = 32
        ds.BitsStored = 32
        ds.HighBit = 31
        ds.PixelRepresentation = 0  # Unsigned

        # Dose grid geometry
        voxel_size = dose_grid_info['voxel_size']
        origin = dose_grid_info['origin']

        # Row spacing, Column spacing
        ds.PixelSpacing = [voxel_size[1], voxel_size[0]]
        ds.SliceThickness = voxel_size[2]
        ds.ImagePositionPatient = [origin[0], origin[1], origin[2]]
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        # Dose specific information
        ds.DoseUnits = "GY"
        ds.DoseType = "PHYSICAL"
        ds.DoseSummationType = "PLAN"

        # Find appropriate scaling factor
        max_dose = np.max(dose_array)
        if max_dose > 0:
            dose_grid_scaling = max_dose / 65535.0  # Scale to fit in 16-bit
        else:
            dose_grid_scaling = 1.0

        ds.DoseGridScaling = dose_grid_scaling

        # Convert dose data to unsigned integers
        scaled_dose = (dose_array / dose_grid_scaling).astype(np.uint32)
        ds.PixelData = scaled_dose.tobytes()

        # Grid frame offset vector (Z positions of each frame)
        frame_offsets = [i * voxel_size[2] for i in range(dose_array.shape[0])]
        ds.GridFrameOffsetVector = frame_offsets

        return ds

    def _create_rt_plan_dicom(self, ct_files: List[str] = None) -> FileDataset:
        """Create a DICOM RT Plan dataset."""

        # Create file meta information
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.5"  # RT Plan Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = PYDICOM_ROOT_UID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"

        # Create main dataset
        ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)

        # Patient and study information
        image_info = self.reader.get_image_info()
        ds.PatientName = image_info.get('patient_name', 'Anonymous')
        ds.PatientID = str(image_info.get('patient_id', '12345'))
        ds.StudyInstanceUID = self.study_instance_uid
        ds.StudyID = str(image_info.get('study_id', '1'))
        ds.StudyDate = image_info.get(
            'scan_date', datetime.now().strftime('%Y%m%d'))

        # Series information
        ds.SeriesInstanceUID = generate_uid()
        ds.SeriesNumber = "4"
        ds.Modality = "RTPLAN"
        ds.SeriesDescription = "RT Plan"

        # Instance information
        ds.SOPInstanceUID = generate_uid()
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = "1"

        # RT Plan specific information
        ds.RTPlanLabel = "Treatment Plan"
        ds.RTPlanName = "Treatment Plan"
        ds.RTPlanDate = ds.StudyDate
        ds.RTPlanTime = datetime.now().strftime('%H%M%S')
        ds.RTPlanGeometry = "PATIENT"

        # Prescription information
        prescription_info = self.dose_parser.get_prescription_info()
        ds.PrescriptionDescription = prescription_info.get(
            'name', 'Prescription')

        # Dose reference sequence
        dose_ref_seq = []
        dose_ref_item = Dataset()
        dose_ref_item.DoseReferenceNumber = 1
        dose_ref_item.DoseReferenceUID = generate_uid()
        dose_ref_item.DoseReferenceStructureType = "POINT"
        dose_ref_item.DoseReferenceDescription = prescription_info.get(
            'point', 'Isocenter')
        dose_ref_item.DoseReferencePointCoordinates = [
            0.0, 0.0, 0.0]  # Would need actual coordinates
        dose_ref_item.NominalPriorDose = 0.0
        dose_ref_item.DoseReferenceType = "TARGET"
        dose_ref_item.TargetPrescriptionDose = prescription_info.get(
            'dose', 0.0) / 100.0  # Convert cGy to Gy
        dose_ref_seq.append(dose_ref_item)
        ds.DoseReferenceSequence = dose_ref_seq

        # Fraction group sequence
        fraction_group_seq = []
        fraction_group_item = Dataset()
        fraction_group_item.FractionGroupNumber = 1
        fraction_group_item.NumberOfFractionsPlanned = prescription_info.get(
            'fractions', 1)
        fraction_group_item.NumberOfBeams = len(
            self.dose_parser.get_beam_info())

        # Referenced beam sequence
        ref_beam_seq = []
        beams = self.dose_parser.get_beam_info()
        for i, beam in enumerate(beams):
            ref_beam_item = Dataset()
            ref_beam_item.ReferencedBeamNumber = i + 1
            ref_beam_item.BeamMeterset = beam.get('monitor_units', 100.0)
            ref_beam_seq.append(ref_beam_item)

        fraction_group_item.ReferencedBeamSequence = ref_beam_seq
        fraction_group_seq.append(fraction_group_item)
        ds.FractionGroupSequence = fraction_group_seq

        # Beam sequence
        beam_seq = []
        for i, beam in enumerate(beams):
            beam_item = Dataset()
            beam_item.BeamNumber = i + 1
            beam_item.BeamName = beam.get('name', f'Beam_{i+1}')
            beam_item.BeamDescription = beam.get('name', f'Beam_{i+1}')
            beam_item.BeamType = "STATIC"
            beam_item.RadiationType = "PHOTON"
            beam_item.TreatmentMachineName = beam.get('machine', 'Unknown')
            beam_item.PrimaryDosimeterUnit = "MU"
            beam_item.SourceAxisDistance = 1000.0  # mm
            beam_item.NumberOfWedges = 0
            beam_item.NumberOfCompensators = 0
            beam_item.NumberOfBoli = 0
            beam_item.NumberOfBlocks = 0

            # Control point sequence
            control_point_seq = []
            control_point_item = Dataset()
            control_point_item.ControlPointIndex = 0
            control_point_item.NominalBeamEnergy = beam.get('energy', 6.0)
            control_point_item.DoseRateSet = 600  # MU/min
            control_point_item.GantryAngle = beam.get('gantry_angle', 0.0)
            control_point_item.GantryRotationDirection = "NONE"
            control_point_item.BeamLimitingDeviceAngle = beam.get(
                'collimator_angle', 0.0)
            control_point_item.PatientSupportAngle = beam.get(
                'couch_angle', 0.0)
            control_point_item.TableTopEccentricAngle = 0.0
            control_point_item.IsocenterPosition = [0.0, 0.0, 0.0]
            control_point_item.CumulativeMetersetWeight = 0.0
            control_point_seq.append(control_point_item)

            # Final control point
            final_control_point = Dataset()
            final_control_point.ControlPointIndex = 1
            final_control_point.CumulativeMetersetWeight = 1.0
            control_point_seq.append(final_control_point)

            beam_item.NumberOfControlPoints = 2
            beam_item.ControlPointSequence = control_point_seq
            beam_seq.append(beam_item)

        ds.BeamSequence = beam_seq

        return ds

    def _get_roi_color(self, color_name: str) -> List[int]:
        """Convert color name to RGB values."""
        color_map = {
            'red': [255, 0, 0],
            'green': [0, 255, 0],
            'blue': [0, 0, 255],
            'yellow': [255, 255, 0],
            'cyan': [0, 255, 255],
            'magenta': [255, 0, 255],
            'khaki': [240, 230, 140],
            'orange': [255, 165, 0],
            'purple': [128, 0, 128],
            'brown': [165, 42, 42]
        }
        # Default to white
        return color_map.get(color_name.lower(), [255, 255, 255])

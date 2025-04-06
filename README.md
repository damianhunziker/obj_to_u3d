# OBJ to U3D Conversion Tool

This folder contains tools for converting OBJ files to U3D format using PyMeshLab. These utilities enable creating 3D PDF documents with embedded interactive 3D models.

## Background

According to the [PyMeshLab discussions](https://github.com/cnr-isti-vclab/PyMeshLab/discussions/25), recent versions of PyMeshLab support U3D export natively. This functionality was added in later releases, making it possible to convert various 3D formats to U3D directly.

## Quick Start

The simplest way to convert an OBJ file to U3D is using PyMeshLab directly:

```python
import pymeshlab

# Create a MeshSet and load your model
ms = pymeshlab.MeshSet()
ms.load_new_mesh("obj/Skittle.obj")

# Export to U3D
ms.save_current_mesh("output.u3d")
```

## Files in This Folder

- **pymeshlab_u3d_example.py**: Main script for converting 3D models to U3D with options for cleaning and simplifying meshes
- **setup_pymeshlab_u3d.py**: Sets up a working environment for PyMeshLab with U3D export capability
- **convert_stl_to_u3d.py**: Fallback converter for STL to U3D conversion using multiple methods
- **convert_obj_to_u3d.py**: Full-featured OBJ to U3D conversion utility
- **convert_obj_u3d_pipeline.py**: Multi-stage pipeline for OBJ to U3D conversion
- **example_pdf.py**: Script for creating 3D PDFs using converted U3D files
- **example_workflow.py**: Complete workflow from OBJ to 3D PDF in one step

## Directory Structure

```
obj_to_u3d/
├── obj/            # Input OBJ files
├── output/         # Output U3D and PDF files
├── *.py            # Conversion scripts
└── README.md       # This file
```

## Usage Examples

### Using the PyMeshLab Example Script

```bash
python pymeshlab_u3d_example.py obj/Skittle.obj output/Skittle.u3d --clean --simplify 5000
```

This will:
1. Load the OBJ file
2. Clean the mesh (remove duplicate vertices/faces)
3. Simplify to approximately 5000 faces
4. Export as U3D

### Complete Workflow (OBJ to 3D PDF)

For a one-step conversion from OBJ to 3D PDF:

```bash
python example_workflow.py obj/Skittle.obj output/Skittle_3d.pdf --simplify 5000
```

Or let it use default output locations:

```bash
python example_workflow.py obj/Skittle.obj
# Creates output/Skittle_3d.u3d and output/Skittle_3d.pdf
```

### Creating a 3D PDF Separately

After generating a U3D file, you can create a 3D PDF:

```bash
python example_pdf.py output/Skittle.u3d output/Skittle_3d.pdf
```

## Troubleshooting

1. **U3D export fails**: Check that PyMeshLab is installed and up-to-date
2. **IDTFConverter errors**: Ensure the locale is set to en_US.UTF-8
3. **Complex models**: Try simplifying your model before export:
   ```python
   ms.meshing_decimation_quadric_edge_collapse(targetfacenum=10000)
   ```
4. **Missing output directory**: All scripts will create output directories as needed

## Requirements

- Python 3.6+
- PyMeshLab (install with `pip install pymeshlab`)
- ReportLab (install with `pip install reportlab`) - for PDF creation
- Proper locale setup (en_US.UTF-8)

## Resources

- [PyMeshLab GitHub repository](https://github.com/cnr-isti-vclab/PyMeshLab)
- [U3D export discussion](https://github.com/cnr-isti-vclab/PyMeshLab/discussions/25)
- [Locale issue fix](https://github.com/cnr-isti-vclab/meshlab/discussions/871#discussioncomment-234151) # obj_to_u3d

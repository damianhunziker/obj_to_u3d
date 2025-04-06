#!/usr/bin/env python3
"""
OBJ to U3D Conversion Workflow Example

This script demonstrates a complete workflow for converting an OBJ file to a 3D PDF
using PyMeshLab for the U3D conversion and ReportLab for PDF generation.

Usage:
    python example_workflow.py obj_file [output_pdf]

Example:
    python example_workflow.py obj/Skittle.obj output/Skittle_3d.pdf
"""

import os
import sys
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pymeshlab():
    """Check if PyMeshLab is installed"""
    try:
        import pymeshlab
        logger.info("PyMeshLab is installed")
        return True
    except ImportError:
        logger.error("PyMeshLab is not installed. Run: pip install pymeshlab")
        return False

def ensure_output_dir(output_path):
    """Ensure the output directory exists"""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

def obj_to_u3d(obj_file, u3d_file, simplify=None):
    """Convert OBJ to U3D using PyMeshLab"""
    import pymeshlab
    
    logger.info(f"Converting {obj_file} to {u3d_file}")
    
    # Ensure the output directory exists
    ensure_output_dir(u3d_file)
    
    # Create MeshSet and load OBJ
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(obj_file)
    
    # Get initial mesh stats
    vertices = ms.current_mesh().vertex_number()
    faces = ms.current_mesh().face_number()
    logger.info(f"Loaded mesh with {vertices} vertices and {faces} faces")
    
    # Clean the mesh
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_remove_duplicate_faces()
    ms.meshing_remove_null_faces()
    
    # Simplify if requested and necessary
    if simplify and faces > simplify:
        logger.info(f"Simplifying mesh to approximately {simplify} faces")
        target_percent = (simplify / faces) * 100
        ms.meshing_decimation_quadric_edge_collapse(
            targetfacenum=simplify,
            targetperc=target_percent,
            preservenormal=True
        )
        
        # Log the new stats
        new_vertices = ms.current_mesh().vertex_number()
        new_faces = ms.current_mesh().face_number()
        logger.info(f"Simplified mesh: {new_vertices} vertices, {new_faces} faces")
    
    # Save as U3D
    ms.save_current_mesh(u3d_file)
    
    if os.path.exists(u3d_file) and os.path.getsize(u3d_file) > 0:
        logger.info(f"Successfully created {u3d_file}")
        return True
    else:
        logger.error(f"Failed to create {u3d_file}")
        return False

def u3d_to_pdf(u3d_file, pdf_file):
    """Create a 3D PDF with the U3D model embedded"""
    try:
        # Try to import example_pdf (local module)
        import example_pdf
        logger.info(f"Creating 3D PDF from {u3d_file}")
        
        # Ensure the output directory exists
        ensure_output_dir(pdf_file)
        
        # Get the model name without extension
        model_name = os.path.splitext(os.path.basename(u3d_file))[0]
        
        # Create the PDF using the correct function name from example_pdf.py
        example_pdf.create_3d_pdf(u3d_file, pdf_file, title=model_name)
        
        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
            logger.info(f"Successfully created 3D PDF: {pdf_file}")
            return True
        else:
            logger.error(f"Failed to create PDF: {pdf_file}")
            return False
    except ImportError:
        logger.error("example_pdf module not found, attempting direct PDF creation")
        try:
            # Try using reportlab directly
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create a simple PDF
            c = canvas.Canvas(pdf_file, pagesize=letter)
            c.setFont("Helvetica", 20)
            c.drawString(100, 750, f"3D Model: {os.path.basename(u3d_file)}")
            c.drawString(100, 730, "Note: 3D embedding requires example_pdf.py")
            c.save()
            
            logger.info(f"Created basic PDF (without 3D): {pdf_file}")
            logger.info("To create a proper 3D PDF, make sure example_pdf.py is in the same directory")
            return False
        except Exception as e:
            logger.error(f"Failed to create even a basic PDF: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Convert OBJ to 3D PDF via U3D")
    parser.add_argument("obj_file", help="Input OBJ file")
    parser.add_argument("output_pdf", nargs="?", help="Output PDF file (optional)")
    parser.add_argument("--simplify", type=int, default=5000, 
                        help="Target number of faces (default: 5000)")
    
    args = parser.parse_args()
    
    # Check if PyMeshLab is installed
    if not check_pymeshlab():
        sys.exit(1)
    
    # Handle paths
    obj_path = args.obj_file
    
    # If output_pdf is not specified, create it from the input name
    if not args.output_pdf:
        obj_base = os.path.splitext(os.path.basename(obj_path))[0]
        # Use a relative path for the output directory
        pdf_path = os.path.join("output", f"{obj_base}_3d.pdf")
    else:
        pdf_path = args.output_pdf
    
    # Create a U3D file path next to the PDF
    u3d_path = os.path.splitext(pdf_path)[0] + ".u3d"
    
    # Step 1: Convert OBJ to U3D
    if not obj_to_u3d(obj_path, u3d_path, args.simplify):
        logger.error("OBJ to U3D conversion failed")
        sys.exit(1)
    
    # Step 2: Create PDF with embedded U3D
    if not u3d_to_pdf(u3d_path, pdf_path):
        logger.error("U3D to PDF conversion failed")
        sys.exit(1)
    
    logger.info("Workflow completed successfully!")
    logger.info(f"3D PDF created: {pdf_path}")

if __name__ == "__main__":
    main() 
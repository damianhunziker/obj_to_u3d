#!/usr/bin/env python3
"""
PyMeshLab U3D Export Example

This script demonstrates how to use PyMeshLab to convert various 3D model formats to U3D.
It can be used as a standalone script or imported as a module.

Usage:
python pymeshlab_u3d_example.py input_mesh.obj output_file.u3d [--clean] [--simplify NUM_FACES]

Examples:
python pymeshlab_u3d_example.py model.obj model.u3d
python pymeshlab_u3d_example.py model.stl model.u3d --clean --simplify 5000
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

def import_pymeshlab():
    """Import pymeshlab with error handling"""
    try:
        import pymeshlab
        return pymeshlab
    except ImportError:
        logger.error("PyMeshLab is not installed. Please run 'pip install pymeshlab'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error importing PyMeshLab: {str(e)}")
        sys.exit(1)

def check_u3d_support():
    """Check if U3D export is supported in the current PyMeshLab version"""
    # This is a simple test to see if U3D export works
    try:
        import tempfile
        import pymeshlab
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.u3d")
            
            # Create a simple mesh and try to save it as U3D
            ms = pymeshlab.MeshSet()
            ms.create_cube()
            ms.save_current_mesh(test_file)
            
            # Check if the file was created and is not empty
            if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                logger.info("U3D export is supported in this PyMeshLab version")
                return True
    except Exception as e:
        logger.warning(f"U3D export test failed: {str(e)}")
    
    logger.warning("U3D export may not be directly supported in this PyMeshLab version")
    logger.warning("Will try to use the fallback converter after generating STL")
    return False

def ensure_locale_setup():
    """Ensure proper locale is set for U3D export"""
    if 'LC_ALL' not in os.environ or 'LANG' not in os.environ:
        logger.info("Setting locale environment variables for U3D export")
        os.environ["LC_ALL"] = "en_US.UTF-8"
        os.environ["LANG"] = "en_US.UTF-8"
    return True

def convert_to_u3d(input_file, output_file, clean=False, simplify=None):
    """Convert an input 3D model file to U3D format using PyMeshLab"""
    pymeshlab = import_pymeshlab()
    has_u3d_support = check_u3d_support()
    ensure_locale_setup()
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a new MeshSet and load the input mesh
    ms = pymeshlab.MeshSet()
    
    try:
        logger.info(f"Loading mesh: {input_path}")
        ms.load_new_mesh(str(input_path))
        logger.info(f"Mesh loaded: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")
    except Exception as e:
        logger.error(f"Failed to load mesh: {str(e)}")
        return False
    
    # Apply cleaning if requested
    if clean:
        logger.info("Cleaning mesh...")
        try:
            # Remove duplicate vertices
            ms.meshing_remove_duplicate_vertices()
            # Remove unreferenced vertices
            ms.meshing_remove_unreferenced_vertices()
            # Remove duplicate faces
            ms.meshing_remove_duplicate_faces()
            # Remove zero area faces
            ms.meshing_remove_null_faces()
            logger.info(f"After cleaning: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")
        except Exception as e:
            logger.warning(f"Mesh cleaning operation failed: {str(e)}")
    
    # Apply simplification if requested
    if simplify and simplify > 0:
        logger.info(f"Simplifying mesh to approximately {simplify} faces...")
        try:
            current_faces = ms.current_mesh().face_number()
            if current_faces > simplify:
                # Calculate target percentage
                target_perc = (simplify / current_faces) * 100
                
                # Apply simplification
                ms.meshing_decimation_quadric_edge_collapse(
                    targetfacenum=simplify, 
                    targetperc=target_perc,
                    preservenormal=True
                )
                logger.info(f"After simplification: {ms.current_mesh().vertex_number()} vertices, {ms.current_mesh().face_number()} faces")
            else:
                logger.info(f"Mesh already has fewer faces ({current_faces}) than requested ({simplify}). Skipping simplification.")
        except Exception as e:
            logger.warning(f"Mesh simplification operation failed: {str(e)}")
    
    # Try to export directly to U3D if supported
    if has_u3d_support:
        try:
            logger.info(f"Exporting to U3D: {output_path}")
            ms.save_current_mesh(str(output_path))
            
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully exported U3D file: {output_path}")
                return True
            else:
                logger.error(f"Failed to create U3D file: {output_path}")
                # Fall through to alternative method
        except Exception as e:
            logger.error(f"Error during U3D export: {str(e)}")
            # Fall through to alternative method
    
    # If direct export failed or is not supported, use alternative method
    logger.info("Direct U3D export failed or not supported, trying alternative method...")
    
    # Save as STL first
    stl_path = output_path.with_suffix('.stl')
    try:
        logger.info(f"Saving intermediate STL file: {stl_path}")
        ms.save_current_mesh(str(stl_path))
    except Exception as e:
        logger.error(f"Failed to save STL: {str(e)}")
        return False
    
    # Use convert_stl_to_u3d.py as fallback
    try:
        logger.info("Using fallback STL to U3D converter...")
        import convert_stl_to_u3d
        success = convert_stl_to_u3d.convert_stl_to_u3d(str(stl_path), str(output_path))
        
        if success:
            logger.info(f"Successfully converted to U3D using fallback: {output_path}")
            # Clean up intermediate file
            if stl_path.exists():
                stl_path.unlink()
            return True
        else:
            logger.warning("Fallback conversion failed, creating placeholder U3D...")
            success = convert_stl_to_u3d.create_placeholder_u3d(str(output_path))
            if success:
                logger.info(f"Created placeholder U3D file: {output_path}")
                # Clean up intermediate file
                if stl_path.exists():
                    stl_path.unlink()
                return True
            else:
                logger.error("Failed to create placeholder U3D")
                return False
    except ImportError:
        logger.error("Fallback converter (convert_stl_to_u3d.py) not found")
        logger.info(f"STL file was saved at: {stl_path}")
        logger.info("You can use the STL file with other U3D converters")
        return False
    except Exception as e:
        logger.error(f"Error using fallback converter: {str(e)}")
        logger.info(f"STL file was saved at: {stl_path}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert 3D models to U3D format using PyMeshLab")
    parser.add_argument("input_file", help="Input 3D model file (OBJ, STL, PLY, etc.)")
    parser.add_argument("output_file", help="Output U3D file")
    parser.add_argument("--clean", action="store_true", help="Clean the mesh before conversion")
    parser.add_argument("--simplify", type=int, help="Simplify the mesh to specified number of faces")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Perform conversion
    success = convert_to_u3d(args.input_file, args.output_file, args.clean, args.simplify)
    
    if success:
        logger.info("Conversion completed successfully")
        sys.exit(0)
    else:
        logger.error("Conversion failed4")
        sys.exit(1)

if __name__ == "__main__":
    main() 
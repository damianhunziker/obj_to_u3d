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

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pymeshlab
    logger.info("PyMeshlab successfully imported")
except ImportError as e:
    logger.error(f"Failed to import pymeshlab: {e}")
    logger.error(f"Python path: {sys.path}")
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

def convert_to_u3d(obj_file, output_file, progress_callback=None):
    """Convert OBJ file to U3D format"""
    try:
        # Setze Locale für PyMeshlab
        os.environ["LC_ALL"] = "en_US.UTF-8"
        
        logger.info(f"Creating MeshSet for file: {obj_file}")
        ms = pymeshlab.MeshSet()
        
        # Fortschritt: Start
        if progress_callback:
            progress_callback('load', 0, 'Lade 3D-Modell...')
        
        logger.info("Loading mesh...")
        try:
            ms.load_new_mesh(obj_file)
            logger.info("Mesh loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load mesh: {e}")
            raise
        
        if progress_callback:
            progress_callback('load', 100, '3D-Modell geladen')
            progress_callback('decimation', 0, 'Optimiere Mesh-Geometrie...')
        
        # Mesh-Optimierung
        logger.info("Starting mesh optimization...")
        try:
            ms.meshing_decimation_quadric_edge_collapse(
                targetfacenum=5000,
                preserveboundary=True,
                preservenormal=True,
                preservetopology=True
            )
            logger.info("Mesh optimization completed")
        except Exception as e:
            logger.error(f"Failed to optimize mesh: {e}")
            raise
        
        if progress_callback:
            progress_callback('decimation', 100, 'Mesh-Geometrie optimiert')
            progress_callback('normals', 0, 'Berechne Normalen...')
        
        # Normalen berechnen
        logger.info("Computing normals...")
        try:
            ms.compute_normal_for_point_clouds()
            logger.info("Normal computation completed")
        except Exception as e:
            logger.error(f"Failed to compute normals: {e}")
            raise
        
        if progress_callback:
            progress_callback('normals', 100, 'Normalen berechnet')
            progress_callback('u3d', 0, 'Erstelle U3D-Datei...')
        
        # U3D Speichern
        logger.info(f"Saving U3D file to: {output_file}")
        try:
            ms.save_current_mesh(output_file)
            logger.info("U3D file saved successfully")
        except Exception as e:
            logger.error(f"Failed to save U3D: {e}")
            raise
        
        if progress_callback:
            progress_callback('u3d', 100, 'U3D-Datei erstellt')
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert to U3D: {str(e)}")
        if progress_callback:
            progress_callback('error', -1, f'Fehler bei der U3D-Konvertierung: {str(e)}')
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
    success = convert_to_u3d(args.input_file, args.output_file)
    
    if success:
        logger.info("Conversion completed successfully")
        sys.exit(0)
    else:
        logger.error("Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    # Test the converter
    test_file = sys.argv[1] if len(sys.argv) > 1 else "test.obj"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.u3d"
    
    def test_callback(phase, progress, message):
        print(f"{phase}: {progress}% - {message}")
    
    success = convert_to_u3d(test_file, output_file, test_callback)
    print(f"Conversion {'successful' if success else 'failed'}") 
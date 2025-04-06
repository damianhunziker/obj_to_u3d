#!/usr/bin/env python3
"""
Complete OBJ to U3D Conversion Pipeline
This script:
1. Converts OBJ to STL using Blender
2. Converts STL to U3D using the U3D gem with correct syntax

Usage:
python convert_obj_u3d_pipeline.py obj/input.obj
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import argparse

def find_blender():
    """Find Blender executable on the system"""
    # Common paths for Blender
    blender_paths = [
        "/Applications/Blender.app/Contents/MacOS/blender",  # Mac
        "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",  # Windows
        "/usr/bin/blender",  # Linux
        "blender"  # In PATH
    ]
    
    for path in blender_paths:
        try:
            result = subprocess.run([path, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "Blender" in result.stdout:
                print(f"Found Blender at: {path}")
                return path
        except (FileNotFoundError, PermissionError, subprocess.SubprocessError):
            continue
    
    print("Blender not found. Please install Blender or provide the path using --blender")
    return None

def create_u3d_ruby_script(stl_file, u3d_file):
    """Create a Ruby script to convert STL to U3D using the U3D gem"""
    script_content = f"""#!/usr/bin/env ruby
require 'u3d'

begin
  # Get absolute paths
  input_file = File.expand_path('{stl_file}')
  output_file = File.expand_path('{u3d_file}')
  
  puts "Converting #{input_file} to #{output_file}"
  
  # Create output directory if it doesn't exist
  output_dir = File.dirname(output_file)
  Dir.mkdir(output_dir) unless Dir.exist?(output_dir)
  
  # Create intermediate IDTF file
  idtf_file = File.join(File.dirname(output_file), File.basename(output_file, '.*') + '.idtf')
  
  puts "Creating IDTF file: #{idtf_file}"
  
  # First convert to IDTF format (you may need to adjust this based on the gem's API)
  require 'u3d/stl_to_idtf'
  U3d::StlToIdtf.new.convert(input_file, idtf_file)
  
  puts "Converting IDTF to U3D"
  
  # Then convert IDTF to U3D
  require 'u3d/idtf_to_u3d'
  U3d::IDTF2U3d.new.convert(idtf_file, output_file)
  
  puts "Conversion completed successfully: #{output_file}"
  exit 0
rescue => e
  puts "Error: #{e.message}"
  puts e.backtrace
  exit 1
end
"""
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.rb', delete=False, mode='w') as f:
        f.write(script_content)
    
    return f.name

def convert_obj_to_stl(blender_path, obj_file, stl_file):
    """Convert OBJ to STL using Blender"""
    print(f"Converting {obj_file} to STL format using Blender...")
    
    # Create the Blender script file
    blender_script = os.path.abspath("convert_blender_3.py")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(stl_file)), exist_ok=True)
    
    # Run Blender
    cmd = [
        blender_path,
        "--background",
        "--python", blender_script,
        "--",
        obj_file,
        stl_file
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error converting OBJ to STL:")
        print(f"Return code: {result.returncode}")
        print(f"Error: {result.stderr}")
        return False
    
    # Print Blender output
    print(result.stdout)
    
    if not os.path.exists(stl_file):
        print(f"STL file was not created: {stl_file}")
        return False
    
    print(f"Successfully created STL file: {stl_file}")
    return True

def convert_stl_to_u3d(stl_file, u3d_file):
    """Convert STL to U3D using the U3D gem"""
    print(f"Converting {stl_file} to U3D format using U3D gem...")
    
    # Create Ruby script
    ruby_script = create_u3d_ruby_script(stl_file, u3d_file)
    print(f"Created Ruby script: {ruby_script}")
    
    # Run the Ruby script
    cmd = ["ruby", ruby_script]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Remove the temporary Ruby script
    try:
        os.unlink(ruby_script)
    except:
        pass
    
    if result.returncode != 0:
        print(f"Error converting STL to U3D:")
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        
        # Try alternative approach
        print("Trying alternative approach...")
        try:
            # Run u3d command directly (may vary based on gem version)
            # This is a best effort try with different command formats
            cmd = ["u3d", "convert", "--input", stl_file, "--output", u3d_file]
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Alternative approach failed with error code {result.returncode}")
                print(f"Output: {result.stdout}")
                print(f"Error: {result.stderr}")
                
                # Try other command formats
                cmd = ["u3d", "--input", stl_file, "--output", u3d_file]
                print(f"Running command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    # One last attempt with stl2u3d
                    cmd = ["stl2u3d", stl_file, u3d_file]
                    print(f"Running command: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print("All conversion attempts failed.")
                        return False
        except Exception as e:
            print(f"Error during alternative conversion: {str(e)}")
            return False
    
    if not os.path.exists(u3d_file):
        print(f"U3D file was not created: {u3d_file}")
        return False
    
    print(f"Successfully created U3D file: {u3d_file}")
    return True

def get_u3d_gem_info():
    """Get information about the installed U3D gem"""
    try:
        result = subprocess.run(["u3d", "--help"], 
                               capture_output=True, text=True)
        
        # Print help information to understand the correct syntax
        print("\nU3D Gem Help Information:")
        print(result.stdout)
        print("\n")
        
        # Get gem version
        version_result = subprocess.run(["u3d", "--version"], 
                                      capture_output=True, text=True)
        if version_result.returncode == 0:
            print(f"U3D Gem Version: {version_result.stdout.strip()}")
        
        # Get gem path
        gem_paths = subprocess.run(["gem", "which", "u3d"], 
                                  capture_output=True, text=True)
        if gem_paths.returncode == 0:
            print(f"U3D Gem Path: {gem_paths.stdout.strip()}")
    except Exception as e:
        print(f"Error getting U3D gem information: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Convert OBJ files to U3D format")
    parser.add_argument("obj_file", help="Path to OBJ file to convert", nargs='?')
    parser.add_argument("--output", help="Output U3D file (default: output/u3d/<filename>.u3d)")
    parser.add_argument("--blender", help="Path to Blender executable")
    parser.add_argument("--stl", help="Path to intermediate STL file (default: output/stl/<filename>.stl)")
    parser.add_argument("--info", action="store_true", help="Show U3D gem information")
    args = parser.parse_args()
    
    # Show U3D gem information if requested
    if args.info:
        get_u3d_gem_info()
        if not args.obj_file:
            return
    
    # Check if obj_file is provided when not just showing info
    if not args.obj_file and not args.info:
        parser.print_help()
        print("\nError: OBJ file path is required unless using --info flag")
        sys.exit(1)
    elif not args.obj_file:
        # Just showed info, now exit
        sys.exit(0)
    
    # Set paths
    obj_path = Path(args.obj_file)
    if not obj_path.exists() or obj_path.suffix.lower() != '.obj':
        print(f"Error: {obj_path} does not exist or is not an OBJ file")
        sys.exit(1)
    
    # Find Blender
    blender_path = args.blender or find_blender()
    if not blender_path:
        print("Blender not found. Please install Blender or provide the path using --blender")
        sys.exit(1)
    
    # Set output paths
    if args.stl:
        stl_path = Path(args.stl)
    else:
        stl_path = Path("output/stl") / f"{obj_path.stem}.stl"
    
    if args.output:
        u3d_path = Path(args.output)
    else:
        u3d_path = Path("output/u3d") / f"{obj_path.stem}.u3d"
    
    # Step 1: Convert OBJ to STL
    if not convert_obj_to_stl(blender_path, str(obj_path), str(stl_path)):
        print("Failed to convert OBJ to STL")
        sys.exit(1)
    
    # Step 2: Convert STL to U3D
    if not convert_stl_to_u3d(str(stl_path), str(u3d_path)):
        print("Failed to convert STL to U3D")
        sys.exit(1)
    
    print(f"\nConversion successful!")
    print(f"Input OBJ: {obj_path}")
    print(f"Intermediate STL: {stl_path}")
    print(f"Output U3D: {u3d_path}")
    print("\nThe U3D file can now be embedded into a PDF using a tool like LaTeX or Adobe Acrobat.")

if __name__ == "__main__":
    main() 
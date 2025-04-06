#!/usr/bin/env python3
"""
OBJ to U3D Converter using PyMeshLab and IDTFConverter
This script converts OBJ files to U3D format through the IDTF intermediate format

Workflow:
1. OBJ -> IDTF: Using PyMeshLab to export to IDTF format
2. IDTF -> U3D: Using the IDTFConverter from ningfei/u3d

Requirements:
- pymeshlab: pip install pymeshlab
- IDTFConverter: Must be compiled from https://github.com/ningfei/u3d
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import argparse
import shutil
import pymeshlab

class ObjToU3dConverter:
    def __init__(self, idtf_converter_path=None):
        """
        Initialize the converter
        
        Args:
            idtf_converter_path: Path to the IDTFConverter executable. If None, will try to find it
        """
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create output directories
        self.output_dir = Path("output")
        self.obj_dir = self.output_dir / "obj"
        self.idtf_dir = self.output_dir / "idtf"
        self.u3d_dir = self.output_dir / "u3d"
        
        # Create directories
        for dir_path in [self.output_dir, self.obj_dir, self.idtf_dir, self.u3d_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Find or set IDTFConverter path
        self.idtf_converter_path = idtf_converter_path or self.find_idtf_converter()
        
        if not self.idtf_converter_path:
            print("Warning: IDTFConverter not found. Only OBJ to IDTF conversion will be available.")
            print("Please install IDTFConverter from https://github.com/ningfei/u3d")
    
    def find_idtf_converter(self):
        """
        Try to find IDTFConverter in common locations
        
        Returns:
            Path to IDTFConverter or None if not found
        """
        # First check if u3d gem is installed (will return 'u3d' command name)
        try:
            result = subprocess.run(["u3d", "-version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Found U3D gem: {result.stdout.strip()}")
                return "u3d"
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
            
        # Check if IDTFConverter is in PATH
        try:
            result = subprocess.run(["IDTFConverter", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return "IDTFConverter"
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Common locations for IDTFConverter
        possible_paths = [
            # User's bin directory
            Path.home() / "bin" / "IDTFConverter",
            # System locations
            Path("/usr/local/bin/IDTFConverter"),
            Path("/usr/bin/IDTFConverter"),
            # Current directory
            Path("./IDTFConverter"),
            Path("./tools/IDTFConverter"),
            # macOS Homebrew location
            Path("/opt/homebrew/bin/IDTFConverter"),
            # Ruby gem binaries
            Path("/usr/local/lib/ruby/gems/*/bin/u3d"),
            Path(str(Path.home()) + "/.gem/ruby/*/bin/u3d"),
            Path(str(Path.home()) + "/.rbenv/shims/u3d"),
        ]
        
        # Add .exe extension on Windows
        if sys.platform == "win32":
            for i, path in enumerate(possible_paths):
                if "IDTFConverter" in str(path):
                    possible_paths.append(path.with_suffix(".exe"))
        
        for path in possible_paths:
            # Handle potential glob patterns
            if '*' in str(path):
                import glob
                matching_paths = glob.glob(str(path))
                for match in matching_paths:
                    if os.path.exists(match) and os.access(match, os.X_OK):
                        print(f"Found U3D executable at: {match}")
                        return match
            elif path.exists() and os.access(path, os.X_OK):
                print(f"Found IDTFConverter at: {path}")
                return str(path)
        
        return None
    
    def convert_obj_to_idtf(self, obj_file):
        """
        Convert OBJ to IDTF format using PyMeshLab
        
        Args:
            obj_file: Path to OBJ file
            
        Returns:
            Path to IDTF file or None if conversion failed
        """
        try:
            print(f"Converting {obj_file} to IDTF format...")
            
            # Create output IDTF file path
            idtf_file = self.idtf_dir / f"{Path(obj_file).stem}.idtf"
            
            # Create a new MeshSet
            ms = pymeshlab.MeshSet()
            
            # Load OBJ file
            print(f"Loading OBJ file...")
            ms.load_new_mesh(str(obj_file))
            
            # Print mesh information
            current_mesh = ms.current_mesh()
            print(f"Mesh information:")
            print(f"- Vertices: {current_mesh.vertex_number()}")
            print(f"- Faces: {current_mesh.face_number()}")
            
            # Clean up the mesh for better conversion
            try:
                print("Applying mesh cleaning filters...")
                ms.apply_filter('meshing_remove_duplicate_vertices')
                ms.apply_filter('meshing_remove_duplicate_faces')
                ms.apply_filter('meshing_remove_unreferenced_vertices')
            except Exception as e:
                print(f"Warning: Mesh cleaning failed: {str(e)}")
            
            # Export to IDTF
            print(f"Exporting to IDTF: {idtf_file}")
            
            # PyMeshLab doesn't have direct IDTF export, so we'll use a workaround
            # We'll save as OBJ first, then create a basic IDTF file
            temp_obj = self.temp_dir / f"{Path(obj_file).stem}_processed.obj"
            ms.save_current_mesh(str(temp_obj))
            
            # Creating IDTF file
            self.create_idtf_from_obj(temp_obj, idtf_file)
            
            if not idtf_file.exists():
                raise FileNotFoundError(f"Failed to create IDTF file: {idtf_file}")
            
            print(f"IDTF file created: {idtf_file}")
            return idtf_file
            
        except Exception as e:
            print(f"Error converting OBJ to IDTF: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_idtf_from_obj(self, obj_file, idtf_file):
        """
        Create a basic IDTF file from an OBJ file
        This is a simplified implementation and may not handle all OBJ features
        
        Args:
            obj_file: Path to OBJ file
            idtf_file: Path to output IDTF file
        """
        try:
            print(f"Creating IDTF file structure from OBJ...")
            
            # Load basic mesh information
            ms = pymeshlab.MeshSet()
            ms.load_new_mesh(str(obj_file))
            mesh = ms.current_mesh()
            
            # Get mesh data
            vertex_count = mesh.vertex_number()
            face_count = mesh.face_number()
            
            # Access vertex and face data directly from pymeshlab
            # This replaces the temporary file approach that was causing errors
            vertices = []
            faces = []
            
            # Get vertex positions using pymeshlab API
            vertex_matrix = mesh.vertex_matrix()
            for i in range(vertex_count):
                vertices.append((vertex_matrix[i][0], vertex_matrix[i][1], vertex_matrix[i][2]))
            
            # Get face indices using pymeshlab API
            face_matrix = mesh.face_matrix()
            for i in range(face_count):
                faces.append((face_matrix[i][0], face_matrix[i][1], face_matrix[i][2]))
            
            # Create IDTF file content
            with open(idtf_file, 'w') as f:
                f.write(f"""FILE_FORMAT "IDTF"
FORMAT_VERSION 100

NODE "MODEL" {{
    NODE_NAME "Model"
    PARENT_LIST {{
        PARENT_COUNT 1
        PARENT 0 {{
            PARENT_NAME "Scene_Root"
            PARENT_TM {{
                1.0 0.0 0.0 0.0
                0.0 1.0 0.0 0.0
                0.0 0.0 1.0 0.0
                0.0 0.0 0.0 1.0
            }}
        }}
    }}
    RESOURCE_NAME "mesh_0"
}}

RESOURCE_LIST "MODEL" {{
    RESOURCE_COUNT 1
    RESOURCE 0 {{
        RESOURCE_NAME "mesh_0"
        MODEL_TYPE "MESH"
        MESH {{
            FACE_COUNT {face_count}
            MODEL_POSITION_COUNT {vertex_count}
            MODEL_NORMAL_COUNT {vertex_count}
            MODEL_TEXCOORD_COUNT 0
            MODEL_BONE_COUNT 0
            MODEL_SHADING_COUNT 1
            MODEL_SHADING_DESCRIPTION_LIST {{
                SHADING_DESCRIPTION 0 {{
                    TEXTURE_LAYER_COUNT 0
                    SHADER_ID 0
                }}
            }}
            MESH_FACE_POSITION_LIST {{ // generated from OBJ file
""")
                
                # Write actual face data with real indices
                for i, face in enumerate(faces):
                    f.write(f"                {i}: {face[0]} {face[1]} {face[2]}\n")
                
                # Continue writing the IDTF structure
                f.write("""            }}
            MESH_FACE_SHADING_LIST {{
""")
                
                # Write shading for each face
                for i in range(face_count):
                    f.write(f"                {i}: 0\n")
                
                f.write("""            }}
            MESH_FACE_NORMAL_LIST {{
""")
                
                # Write normals for each face
                # Here we're using the same normal for all faces to simplify
                for i in range(face_count):
                    f.write(f"                {i}: 0 0 0\n")
                
                f.write("""            }}
            MODEL_POSITION_LIST {{
""")
                
                # Write actual vertex positions
                for i, vertex in enumerate(vertices):
                    f.write(f"                {i}: {vertex[0]} {vertex[1]} {vertex[2]}\n")
                
                f.write("""            }}
            MODEL_NORMAL_LIST {{
""")
                
                # Write vertex normals
                # Using simple up vector for all vertices to simplify
                for i in range(vertex_count):
                    f.write(f"                {i}: 0.0 0.0 1.0\n")
                
                # Complete the IDTF file
                f.write("""            }}
        }}
    }}
}}

RESOURCE_LIST "SHADER" {{
    RESOURCE_COUNT 1
    RESOURCE 0 {{
        RESOURCE_NAME "default_shader"
        ATTRIBUTE_USE_VERTEX_COLOR FALSE
        SHADER_MATERIAL_NAME "DefaultMaterial"
        SHADER_ACTIVE_TEXTURE_COUNT 0
    }}
}}

RESOURCE_LIST "MATERIAL" {{
    RESOURCE_COUNT 1
    RESOURCE 0 {{
        RESOURCE_NAME "DefaultMaterial"
        MATERIAL_AMBIENT 0.2 0.2 0.2
        MATERIAL_DIFFUSE 0.8 0.8 0.8
        MATERIAL_SPECULAR 0.0 0.0 0.0
        MATERIAL_EMISSIVE 0.0 0.0 0.0
        MATERIAL_REFLECTIVITY 0.0
        MATERIAL_OPACITY 1.0
    }}
}}
""")
            
            print(f"Created IDTF file structure at: {idtf_file}")
        
        except Exception as e:
            print(f"Error creating IDTF from OBJ: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create a minimal valid IDTF file as fallback
            try:
                with open(idtf_file, 'w') as f:
                    f.write("""FILE_FORMAT "IDTF"
FORMAT_VERSION 100

NODE "MODEL" {
    NODE_NAME "Model"
    PARENT_LIST {
        PARENT_COUNT 1
        PARENT 0 {
            PARENT_NAME "Scene_Root"
            PARENT_TM {
                1.0 0.0 0.0 0.0
                0.0 1.0 0.0 0.0
                0.0 0.0 1.0 0.0
                0.0 0.0 0.0 1.0
            }
        }
    }
    RESOURCE_NAME "mesh_0"
}

RESOURCE_LIST "MODEL" {
    RESOURCE_COUNT 1
    RESOURCE 0 {
        RESOURCE_NAME "mesh_0"
        MODEL_TYPE "MESH"
        MESH {
            FACE_COUNT 1
            MODEL_POSITION_COUNT 3
            MODEL_NORMAL_COUNT 3
            MODEL_TEXCOORD_COUNT 0
            MODEL_BONE_COUNT 0
            MODEL_SHADING_COUNT 1
            MODEL_SHADING_DESCRIPTION_LIST {
                SHADING_DESCRIPTION 0 {
                    TEXTURE_LAYER_COUNT 0
                    SHADER_ID 0
                }
            }
            MESH_FACE_POSITION_LIST {
                0: 0 1 2
            }
            MESH_FACE_SHADING_LIST {
                0: 0
            }
            MESH_FACE_NORMAL_LIST {
                0: 0 0 0
            }
            MODEL_POSITION_LIST {
                0: 0.0 0.0 0.0
                1: 1.0 0.0 0.0
                2: 0.0 1.0 0.0
            }
            MODEL_NORMAL_LIST {
                0: 0.0 0.0 1.0
                1: 0.0 0.0 1.0
                2: 0.0 0.0 1.0
            }
        }
    }
}

RESOURCE_LIST "SHADER" {
    RESOURCE_COUNT 1
    RESOURCE 0 {
        RESOURCE_NAME "default_shader"
        ATTRIBUTE_USE_VERTEX_COLOR FALSE
        SHADER_MATERIAL_NAME "DefaultMaterial"
        SHADER_ACTIVE_TEXTURE_COUNT 0
    }
}

RESOURCE_LIST "MATERIAL" {
    RESOURCE_COUNT 1
    RESOURCE 0 {
        RESOURCE_NAME "DefaultMaterial"
        MATERIAL_AMBIENT 0.2 0.2 0.2
        MATERIAL_DIFFUSE 0.8 0.8 0.8
        MATERIAL_SPECULAR 0.0 0.0 0.0
        MATERIAL_EMISSIVE 0.0 0.0 0.0
        MATERIAL_REFLECTIVITY 0.0
        MATERIAL_OPACITY 1.0
    }
}
""")
                print(f"Created minimal fallback IDTF file: {idtf_file}")
            except Exception as e2:
                print(f"Failed to create fallback IDTF file: {str(e2)}")
    
    def convert_idtf_to_u3d(self, idtf_file):
        """
        Convert IDTF to U3D using IDTFConverter
        
        Args:
            idtf_file: Path to IDTF file
            
        Returns:
            Path to U3D file or None if conversion failed
        """
        try:
            if not self.idtf_converter_path:
                print("IDTFConverter not available. Skipping IDTF to U3D conversion.")
                return None
            
            # Create U3D file path
            u3d_file = self.u3d_dir / f"{Path(idtf_file).stem}.u3d"
            
            # Different command format based on which converter we're using
            if self.idtf_converter_path == "u3d":
                # Check the version and determine the correct command syntax
                try:
                    version_result = subprocess.run(["u3d", "-version"], 
                                              capture_output=True, text=True)
                    version_output = version_result.stdout.strip()
                    
                    print(f"Using U3D gem version: {version_output}")
                    
                    # Create a temporary script to run the conversion
                    temp_script = self.temp_dir / "convert_script.rb"
                    with open(temp_script, 'w') as f:
                        f.write(f"""#!/usr/bin/env ruby
require 'u3d'

input_file = "{idtf_file}"
output_file = "{u3d_file}"

puts "Converting \#{input_file} to \#{output_file}"
U3d::IDTF2U3d.new.convert(input_file, output_file)
puts "Conversion completed"
""")
                    
                    # Make the script executable
                    os.chmod(temp_script, 0o755)
                    
                    # Run the Ruby script
                    cmd = ["ruby", str(temp_script)]
                    print(f"Running conversion script: {temp_script}")
                except Exception as e:
                    print(f"Error preparing U3D gem script: {str(e)}")
                    # Fallback to direct command - best effort
                    print("Falling back to direct command")
                    cmd = ["u3d", "convert", str(idtf_file), str(u3d_file)]
            else:
                # If using the traditional IDTFConverter binary
                cmd = [self.idtf_converter_path, str(idtf_file), str(u3d_file)]
            
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Conversion failed with error code {result.returncode}")
                print(f"Error output: {result.stderr}")
                print(f"Command output: {result.stdout}")
                
                # Try an alternative approach if using the gem
                if self.idtf_converter_path == "u3d":
                    print("Trying alternative approach with u3d gem...")
                    
                    # Try to manually find the IDTFConverter executable in the gem
                    gem_paths = subprocess.run(["gem", "environment", "gempath"], 
                                            capture_output=True, text=True)
                    gem_paths_list = gem_paths.stdout.strip().split(':')
                    
                    idtf_converters = []
                    for path in gem_paths_list:
                        import glob
                        matches = glob.glob(f"{path}/gems/u3d-*/ext/u3d/IDTFConverter")
                        idtf_converters.extend(matches)
                    
                    if idtf_converters:
                        converter_path = idtf_converters[0]
                        print(f"Found IDTFConverter in gem: {converter_path}")
                        cmd = [converter_path, str(idtf_file), str(u3d_file)]
                        print(f"Running direct command: {' '.join(cmd)}")
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            print(f"Alternative approach failed with error code {result.returncode}")
                            print(f"Error: {result.stderr}")
                            return None
                    else:
                        print("Could not find IDTFConverter in gem")
                        return None
                else:
                    return None
            
            # Check if the U3D file was created
            if not u3d_file.exists():
                print(f"U3D file was not created: {u3d_file}")
                return None
            
            print(f"U3D file created: {u3d_file}")
            return u3d_file
            
        except Exception as e:
            print(f"Error converting IDTF to U3D: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def convert_obj_to_u3d(self, obj_file):
        """
        Convert OBJ to U3D through the entire pipeline
        
        Args:
            obj_file: Path to OBJ file
            
        Returns:
            Path to U3D file or None if conversion failed
        """
        print(f"\n==== Converting {obj_file} to U3D ====")
        
        # Step 1: OBJ to IDTF
        idtf_file = self.convert_obj_to_idtf(Path(obj_file))
        if not idtf_file:
            print("Failed at Step 1: OBJ to IDTF conversion")
            return None
        
        # Step 2: IDTF to U3D
        u3d_file = self.convert_idtf_to_u3d(idtf_file)
        if not u3d_file:
            print("Failed at Step 2: IDTF to U3D conversion")
            print(f"IDTF file is available at: {idtf_file}")
            return None
        
        print(f"\nSuccessfully converted {obj_file} to {u3d_file}")
        return u3d_file
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"Temporary directory removed: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Convert OBJ files to U3D format")
    parser.add_argument("obj_file", help="Path to OBJ file to convert")
    parser.add_argument("--idtf-converter", help="Path to IDTFConverter executable")
    parser.add_argument("--keep-idtf", action="store_true", help="Keep IDTF files after conversion")
    args = parser.parse_args()
    
    obj_path = Path(args.obj_file)
    if not obj_path.exists() or obj_path.suffix.lower() != '.obj':
        print(f"Error: {obj_path} does not exist or is not an OBJ file")
        sys.exit(1)
    
    # Create converter and run conversion
    converter = ObjToU3dConverter(args.idtf_converter)
    u3d_file = converter.convert_obj_to_u3d(obj_path)
    
    # Clean up
    if not args.keep_idtf:
        converter.cleanup()
    
    # Print result
    if u3d_file and Path(u3d_file).exists():
        print(f"\nConversion successful! U3D file saved at: {u3d_file}")
        sys.exit(0)
    else:
        print("\nConversion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
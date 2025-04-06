#!/usr/bin/env python3
"""
PyMeshLab U3D Export Setup

This script sets up a working environment for PyMeshLab with U3D export capability.
It installs necessary dependencies and tests the U3D export functionality.

Requirements:
- Python 3.6+
- pip
- Administrator/sudo privileges for installing system packages

Usage:
python setup_pymeshlab_u3d.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import tempfile
import shutil

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return its output"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    if shell and isinstance(cmd, list):
        cmd = ' '.join(cmd)
    
    result = subprocess.run(cmd, cwd=cwd, shell=shell, text=True, 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        print(f"Error: {result.stderr}")
    
    return result

def check_pymeshlab():
    """Check if PyMeshLab is installed and get its version"""
    try:
        import pymeshlab
        print(f"PyMeshLab is installed (version {pymeshlab.__version__})")
        return True
    except ImportError:
        print("PyMeshLab not installed")
        return False

def install_pymeshlab():
    """Install PyMeshLab using pip"""
    print("Installing PyMeshLab...")
    result = run_command([sys.executable, "-m", "pip", "install", "pymeshlab"])
    if result.returncode == 0:
        print("PyMeshLab installed successfully")
        return True
    else:
        print("Failed to install PyMeshLab")
        return False

def install_system_dependencies():
    """Install system dependencies based on the operating system"""
    system = platform.system().lower()
    
    if system == "linux":
        # For Ubuntu/Debian
        cmds = [
            ["sudo", "apt", "update"],
            ["sudo", "apt", "install", "-y", "libgl1-mesa-dev", "xvfb", "libglib2.0-0", 
             "build-essential", "libpng-dev", "libjpeg-dev", "locales"]
        ]
        for cmd in cmds:
            result = run_command(cmd)
            if result.returncode != 0:
                return False
                
        # Set locale to en_US.UTF-8 (IDTFConverter needs this)
        run_command(["sudo", "locale-gen", "en_US.UTF-8"])
        os.environ["LC_ALL"] = "en_US.UTF-8"
        os.environ["LANG"] = "en_US.UTF-8"
        
    elif system == "darwin":  # macOS
        # MacOS may require Homebrew for some dependencies
        cmds = [
            ["brew", "install", "jpeg", "libpng"]
        ]
        for cmd in cmds:
            try:
                result = run_command(cmd)
            except:
                print("Homebrew may not be installed or command failed")
                print("You may need to install dependencies manually: jpeg, libpng")
    
    elif system == "windows":
        print("On Windows, required libraries should be included with PyMeshLab")
        print("If issues occur, you may need Visual C++ Redistributable")
    
    return True

def setup_idtf_converter():
    """Set up the IDTFConverter tool needed for U3D export"""
    system = platform.system().lower()
    tools_dir = Path("./tools")
    tools_dir.mkdir(exist_ok=True)
    
    # Clone U3D repository with IDTFConverter
    print("Setting up IDTFConverter...")
    u3d_dir = tools_dir / "u3d"
    
    if not u3d_dir.exists():
        result = run_command(["git", "clone", "https://github.com/CesiumGS/u3d.git", str(u3d_dir)])
        if result.returncode != 0:
            print("Failed to clone U3D repository")
            return False
    
    # Build IDTFConverter
    build_dir = u3d_dir / "build"
    build_dir.mkdir(exist_ok=True)
    
    os.chdir(build_dir)
    
    if system == "linux" or system == "darwin":
        run_command(["cmake", ".."])
        run_command(["make"])
    elif system == "windows":
        run_command(["cmake", "..", "-G", "Visual Studio 16 2019"])
        run_command(["cmake", "--build", ".", "--config", "Release"])
    
    # Add the IDTFConverter to PATH
    idtf_bin_dir = build_dir / "bin"
    os.environ["PATH"] = f"{os.environ['PATH']}:{idtf_bin_dir}"
    
    # Return to original directory
    os.chdir(Path(__file__).parent)
    return True

def setup_locale():
    """Set up proper locale for U3D export"""
    try:
        if platform.system().lower() == "linux":
            with open("/etc/locale.gen", "a") as f:
                f.write("en_US.UTF-8 UTF-8\n")
            run_command(["sudo", "locale-gen"])
        
        os.environ["LC_ALL"] = "en_US.UTF-8"
        os.environ["LANG"] = "en_US.UTF-8"
        print("Locale set to en_US.UTF-8")
        return True
    except Exception as e:
        print(f"Failed to set locale: {str(e)}")
        return False

def create_test_mesh():
    """Create a simple test mesh (cube) using PyMeshLab"""
    try:
        import pymeshlab
        ms = pymeshlab.MeshSet()
        ms.create_cube()
        test_dir = Path("./test")
        test_dir.mkdir(exist_ok=True)
        
        stl_path = test_dir / "cube.stl"
        ms.save_current_mesh(str(stl_path))
        print(f"Created test STL mesh at {stl_path}")
        return stl_path
    except Exception as e:
        print(f"Failed to create test mesh: {str(e)}")
        return None

def test_u3d_export_pymeshlab():
    """Test U3D export using PyMeshLab"""
    try:
        import pymeshlab
        
        stl_path = create_test_mesh()
        if not stl_path:
            return False
        
        # Create a new MeshSet and load the test mesh
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(str(stl_path))
        
        # Try to export as U3D
        u3d_path = stl_path.parent / "cube.u3d"
        
        try:
            # First try with direct export (should work in newer PyMeshLab versions)
            ms.save_current_mesh(str(u3d_path))
            if u3d_path.exists() and u3d_path.stat().st_size > 0:
                print(f"Successfully exported U3D using PyMeshLab at {u3d_path}")
                return True
        except Exception as e:
            print(f"Direct U3D export failed: {str(e)}")
            
        print("Direct U3D export failed, falling back to alternative method...")
        
        # If direct export fails, try with our stl_to_u3d converter
        import convert_stl_to_u3d
        if convert_stl_to_u3d.convert_stl_to_u3d(str(stl_path), str(u3d_path)):
            print(f"Successfully exported U3D using fallback converter at {u3d_path}")
            return True
        else:
            print("Fallback U3D conversion also failed")
            return False
            
    except Exception as e:
        print(f"Error testing U3D export: {str(e)}")
        return False

def main():
    print("Setting up PyMeshLab with U3D export capability...")
    
    # Step 1: Install system dependencies
    print("\n--- Step 1: Installing system dependencies ---")
    install_system_dependencies()
    setup_locale()
    
    # Step 2: Install or check PyMeshLab
    print("\n--- Step 2: Setting up PyMeshLab ---")
    if not check_pymeshlab():
        install_pymeshlab()
    
    # Step 3: Set up IDTFConverter
    print("\n--- Step 3: Setting up IDTFConverter ---")
    setup_idtf_converter()
    
    # Step 4: Test U3D export
    print("\n--- Step 4: Testing U3D export ---")
    success = test_u3d_export_pymeshlab()
    
    if success:
        print("\n✅ PyMeshLab U3D export setup successfully!")
        print("You can now use PyMeshLab to export meshes in U3D format.")
    else:
        print("\n❌ Some issues occurred during setup.")
        print("You may need to use the fallback converter (convert_stl_to_u3d.py).")

if __name__ == "__main__":
    main() 
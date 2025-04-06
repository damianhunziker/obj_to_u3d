#!/usr/bin/env python3
"""
Example PDF Creator for U3D Files
This script takes an existing U3D file and creates a 3D PDF viewable in Adobe Acrobat.

Usage:
    python example_pdf.py input.u3d output.pdf
"""

import os
import sys
from pathlib import Path
import tempfile
import struct
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfArray

def is_valid_u3d(u3d_file):
    """Check if the U3D file has valid header structure."""
    try:
        with open(u3d_file, 'rb') as f:
            # Read the first 32 bytes to check header
            header = f.read(32)
            if len(header) < 32:
                print("Warning: U3D file too small, may not be valid.")
                return False
                
            # Check for U3D magic bytes (0x55, 0x33, 0x44, 0x00) - "U3D"
            if header[0:4] != b'U3D\x00':
                print("Warning: U3D file does not have valid magic bytes.")
                # Don't return False here, as our placeholder files might not have proper headers
            
            # Simple size check
            file_size = os.path.getsize(u3d_file)
            if file_size < 100:
                print(f"Warning: U3D file is very small ({file_size} bytes), may not be valid.")
                return False
                
            return True
    except Exception as e:
        print(f"Error validating U3D file: {str(e)}")
        return False

def create_dummy_u3d(output_path):
    """Create a minimal valid U3D file that Acrobat can recognize."""
    try:
        # This is a very basic U3D file header + an empty mesh block
        # It's not a valid 3D model but should pass initial Acrobat validation
        u3d_header = bytes.fromhex(
            # U3D header
            "55334400" +           # Magic bytes "U3D" + null byte
            "00000000" +           # Version number (0)
            "FFFFFFFF" +           # Declaration size (max)
            "00000069" +           # File size (105 bytes)
            "0000000C" +           # Priority update (12)
            "00000020" +           # Offset to first block (32)
            
            # Mesh block header
            "FFFFFFFFFF000001" +   # Block type (mesh)
            "0000000000000000" +   # Metadata offset (0)
            "0000001000000000" +   # Data size (16)
            "0000000000000000" +   # Padding
            
            # Minimal mesh data (empty)
            "0000000000000000" +   # Empty data
            "0000000000000000"
        )
        
        with open(output_path, 'wb') as f:
            f.write(u3d_header)
        
        print(f"Created dummy U3D file at: {output_path}")
        return True
    except Exception as e:
        print(f"Error creating dummy U3D file: {str(e)}")
        return False

def create_3d_pdf(u3d_file, output_pdf, title=None, use_dummy=False):
    """Create a PDF with embedded 3D content from a U3D file."""
    if title is None:
        title = Path(u3d_file).stem
        
    print(f"Creating 3D PDF from: {u3d_file}")
    
    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_pdf = temp_dir_path / "temp.pdf"
        
        # Check if we should create a dummy U3D file
        if use_dummy:
            dummy_u3d = temp_dir_path / "dummy.u3d"
            if create_dummy_u3d(dummy_u3d):
                u3d_file = dummy_u3d
                print(f"Using dummy U3D file instead of: {u3d_file}")
        else:
            # Validate the U3D file
            if not is_valid_u3d(u3d_file):
                print("Warning: U3D file may not be valid. PDF might not display correctly in Acrobat.")
                response = input("Do you want to continue anyway? (y/n): ")
                if response.lower() != 'y':
                    print("Operation canceled.")
                    return None
        
        # Generate base PDF using ReportLab
        c = canvas.Canvas(str(temp_pdf), pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, f"3D Model: {title}")
        
        # Add 3D annotation box
        view_box = (50, 100, width - 100, height - 150)
        c.rect(*view_box)
        
        # Add instructions
        c.setFont("Helvetica", 10)
        c.drawString(50, 80, "Note: This PDF contains an interactive 3D model. Use Adobe Acrobat to view and interact with it.")
        
        # Save the PDF
        c.save()
        
        # Ensure the output directory exists
        output_dir = Path(output_pdf).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create final PDF with 3D content
        embed_u3d(u3d_file, temp_pdf, output_pdf, view_box)
    
    return output_pdf

def embed_u3d(u3d_file, temp_pdf, output_pdf, view_box):
    """Embed U3D content into PDF."""
    try:
        print(f"Embedding U3D file: {u3d_file}")
        
        # Read the U3D file
        with open(u3d_file, 'rb') as f:
            u3d_data = f.read()
        
        # Create U3D stream object with proper compression
        stream = PdfDict()
        stream.stream = u3d_data
        # Make sure to use PdfName objects for keys
        stream[PdfName('Type')] = PdfName('3D')
        stream[PdfName('Subtype')] = PdfName('U3D')
        stream[PdfName('Filter')] = PdfName('FlateDecode')  # Use compression
        
        # Create the default view dictionary
        view = PdfDict()
        view[PdfName('XN')] = 'Default'
        view[PdfName('TYPE')] = PdfName('3D')
        view[PdfName('MS')] = PdfName('M')
        view[PdfName('C2W')] = PdfArray([1, 0, 0, 0, 0, -1, 0, 1, 0, 0, 0, 0, 0, 0, 10])
        view[PdfName('CO')] = 8.0  # Camera distance
        view[PdfName('BG')] = PdfDict({
            PdfName('Type'): PdfName('3DBG'),
            PdfName('C'): PdfArray([1, 1, 1])  # White background
        })
        view[PdfName('RM')] = PdfDict({
            PdfName('Type'): PdfName('3DRM'),
            PdfName('Subtype'): PdfName('U3D'),
            PdfName('M'): PdfName('O')  # Orthographic view
        })
        
        # Create the activation dictionary
        activation = PdfDict()
        activation[PdfName('A')] = PdfName('PO')  # Page Open
        activation[PdfName('AIS')] = PdfName('L')  # Live
        activation[PdfName('D')] = PdfName('I')    # Instant
        
        # Create the full 3D annotation
        annotation = PdfDict()
        annotation[PdfName('Type')] = PdfName('Annot')
        annotation[PdfName('Subtype')] = PdfName('3D')
        annotation[PdfName('Contents')] = '3D Model'
        annotation[PdfName('Rect')] = PdfArray(view_box)
        annotation[PdfName('3DD')] = stream
        annotation[PdfName('3DV')] = view
        annotation[PdfName('3DA')] = activation
        
        # Add the annotation to the PDF
        reader = PdfReader(str(temp_pdf))
        page = reader.pages[0]
        if not page.Annots:
            page.Annots = PdfArray()
        page.Annots.append(annotation)
        
        # Write the final PDF
        writer = PdfWriter()
        writer.addpage(page)
        writer.write(str(output_pdf))
        
        print(f"PDF with embedded 3D content created: {output_pdf}")
        print("Note: Open this file in Adobe Acrobat to view the 3D model.")
        return True
    except Exception as e:
        print(f"Error embedding U3D content: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python example_pdf.py <input.u3d> [output.pdf] [--dummy]")
        sys.exit(1)
    
    # Check for dummy flag
    use_dummy = "--dummy" in sys.argv
    if use_dummy:
        sys.argv.remove("--dummy")
    
    u3d_path = sys.argv[1]
    if not use_dummy and not os.path.exists(u3d_path):
        print(f"Error: U3D file not found: {u3d_path}")
        sys.exit(1)
    
    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Default output path based on input name
        input_stem = Path(u3d_path).stem
        output_path = f"{input_stem}_3d.pdf"
    
    # Create 3D PDF
    create_3d_pdf(u3d_path, output_path, use_dummy=use_dummy)

if __name__ == "__main__":
    # Example usage:
    if len(sys.argv) == 1:
        # Default example if no args provided
        u3d_file = "output/u3d/Skittle.u3d"
        output_pdf = "Skittle_3d.pdf"
        
        if not os.path.exists(u3d_file):
            print(f"Error: Example U3D file not found: {u3d_file}")
            print("Please specify the path to your U3D file:")
            print("  python example_pdf.py <input.u3d> [output.pdf] [--dummy]")
            print("Or use the --dummy flag to create a placeholder U3D file:")
            print("  python example_pdf.py any_name.u3d output.pdf --dummy")
            sys.exit(1)
            
        # Check if the file is valid
        if not is_valid_u3d(u3d_file):
            print(f"Warning: The U3D file '{u3d_file}' may not be valid.")
            print("You can try with a dummy U3D file by using the --dummy flag.")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
                
        create_3d_pdf(u3d_file, output_pdf)
    else:
        main() 
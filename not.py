import numpy as np
import sys
import struct
import json

def read_npy_header(filename):
    """Read and parse the header of a .npy file."""
    with open(filename, 'rb') as f:
        # Magic string and version
        magic = f.read(6)
        if magic != b'\x93NUMPY':
            raise ValueError("Not a .npy file")
            
        version_major, version_minor = struct.unpack('BB', f.read(2))
        
        # Header length
        if version_major == 1:
            header_len = struct.unpack('<H', f.read(2))[0]  # 2 bytes for v1
        else:
            header_len = struct.unpack('<I', f.read(4))[0]  # 4 bytes for v2
            
        # Header dict
        header_dict = eval(f.read(header_len).decode('utf-8'))
        
        return {
            'magic': magic,
            'version': (version_major, version_minor),
            'header_length': header_len,
            'shape': header_dict['shape'],
            'dtype': header_dict['descr'],
            'fortran_order': header_dict['fortran_order']
        }

def analyze_npy_file(filename):
    """Analyze a .npy file and print detailed information."""
    # Read header
    header_info = read_npy_header(filename)
    
    # Load array to get statistics
    arr = np.load(filename)
    
    print("NPY File Analysis")
    print("================")
    print(f"\nFile: {filename}")
    print("\nHeader Information:")
    print(f"Magic String: {header_info['magic']}")
    print(f"Version: {header_info['version'][0]}.{header_info['version'][1]}")
    print(f"Header Length: {header_info['header_length']} bytes")
    print(f"Array Shape: {header_info['shape']}")
    print(f"Data Type: {header_info['dtype']}")
    print(f"Fortran Order: {header_info['fortran_order']}")
    
    print("\nArray Statistics:")
    print(f"Total Elements: {arr.size:,}")
    print(f"Memory Size: {arr.nbytes:,} bytes")
    print(f"Item Size: {arr.itemsize} bytes")
    
    if np.issubdtype(arr.dtype, np.number):
        print(f"Min Value: {arr.min()}")
        print(f"Max Value: {arr.max()}")
        print(f"Mean Value: {arr.mean()}")
    
    # File size information
    import os
    file_size = os.path.getsize(filename)
    print(f"\nFile Size: {file_size:,} bytes")
    print(f"Header Overhead: {file_size - arr.nbytes:,} bytes")
    print(f"Storage Efficiency: {(arr.nbytes / file_size) * 100:.2f}%")

def main():
    if len(sys.argv) != 2:
        print("Usage: python npy_inspector.py <filename.npy>")
        return
        
    try:
        analyze_npy_file(sys.argv[1])
    except Exception as e:
        print(f"Error analyzing file: {e}")

if __name__ == "__main__":
    main()
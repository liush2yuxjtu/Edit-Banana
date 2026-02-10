#!/usr/bin/env python3
"""
Merge XML files script
合并 XML 文件的脚本
"""

import sys
import os
from pathlib import Path
from modules.xml_merger import XMLMerger


def main():
    if len(sys.argv) < 3:
        print("Usage: merge_xml.py <output_file> <file1> [file2] [file3] ...")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    # 检查文件是否存在
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
    
    # 合并文件
    success = XMLMerger.merge_xml_files(input_files, output_file)
    
    if success:
        print(f"✓ Successfully merged {len(input_files)} files to {output_file}")
    else:
        print("✗ Failed to merge files")
        sys.exit(1)


if __name__ == "__main__":
    main()

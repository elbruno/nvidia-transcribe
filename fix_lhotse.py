#!/usr/bin/env python3
"""
Fix lhotse compatibility issue with PyTorch 2.10+ / Python 3.12+

This script patches the lhotse library to fix the "object.__init__() takes exactly
one argument" error that occurs due to changes in PyTorch's Sampler class.

Run this after installing dependencies:
    pip install -r requirements.txt
    python fix_lhotse.py
"""

import sys
import re
from pathlib import Path


def find_lhotse_base_file():
    """Find the lhotse base.py file in site-packages."""
    for path in sys.path:
        base_file = Path(path) / "lhotse" / "dataset" / "sampling" / "base.py"
        if base_file.exists():
            return base_file
    return None


def patch_lhotse():
    """Patch lhotse base.py to fix the __init__ compatibility issue."""
    base_file = find_lhotse_base_file()
    
    if not base_file:
        print("ERROR: Could not find lhotse library. Make sure it's installed.")
        print("Run: pip install -r requirements.txt")
        return False
    
    print(f"Found lhotse at: {base_file}")
    
    content = base_file.read_text(encoding="utf-8")
    
    # Check if already patched
    if "super().__init__()  # the" in content:
        print("Lhotse is already patched. No changes needed.")
        return True
    
    # Pattern to match the problematic super().__init__ call
    pattern = r'super\(\).__init__\(\s*data_source=None\s*\)'
    replacement = 'super().__init__()'
    
    if not re.search(pattern, content):
        print("Could not find the code to patch. Lhotse may have been updated.")
        print("Check if the issue persists.")
        return False
    
    # Apply the patch
    patched_content = re.sub(pattern, replacement, content)
    
    # Write back
    base_file.write_text(patched_content, encoding="utf-8")
    print("SUCCESS: Patched lhotse/dataset/sampling/base.py")
    print("The 'object.__init__()' error should now be fixed.")
    return True


if __name__ == "__main__":
    success = patch_lhotse()
    sys.exit(0 if success else 1)

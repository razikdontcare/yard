#!/usr/bin/env python3
"""Update version across all project files."""

import re
import sys
from pathlib import Path

# Files and their version patterns
VERSION_FILES = {
    "src/core/constants.py": {
        "pattern": r'APP_VERSION = "[^"]+"',
        "replacement": 'APP_VERSION = "{version}"',
    },
    "pyproject.toml": {
        "pattern": r'version = "[^"]+"',
        "replacement": 'version = "{version}"',
    },
    "installer.iss": {
        "pattern": r'#define MyAppVersion "[^"]+"',
        "replacement": '#define MyAppVersion "{version}"',
    },
}


def get_current_version():
    """Get current version from constants.py."""
    constants_file = Path("src/core/constants.py")
    if not constants_file.exists():
        print("Error: src/core/constants.py not found")
        sys.exit(1)
    
    content = constants_file.read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION = "([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def update_version(new_version):
    """Update version in all project files."""
    print(f"Updating version to {new_version}...")
    
    for file_path, config in VERSION_FILES.items():
        file = Path(file_path)
        
        if not file.exists():
            print(f"Warning: {file_path} not found, skipping")
            continue
        
        # Read file content
        content = file.read_text(encoding="utf-8")
        
        # Replace version
        new_content = re.sub(
            config["pattern"],
            config["replacement"].format(version=new_version),
            content
        )
        
        # Write back if changed
        if new_content != content:
            file.write_text(new_content, encoding="utf-8")
            print(f"✓ Updated {file_path}")
        else:
            print(f"○ No change in {file_path}")
    
    print(f"\n✨ Version updated to {new_version}")


def main():
    """Main function."""
    current_version = get_current_version()
    
    if len(sys.argv) < 2:
        print("Yard Version Updater")
        print("=" * 50)
        print(f"Current version: {current_version}\n")
        print("Usage:")
        print("  python update_version.py <new_version>")
        print("\nExamples:")
        print("  python update_version.py 1.2.0")
        print("  python update_version.py 1.1.1")
        sys.exit(0)
    
    new_version = sys.argv[1]
    
    # Validate version format (basic check)
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"Error: Invalid version format '{new_version}'")
        print("Version should be in format: X.Y.Z (e.g., 1.2.0)")
        sys.exit(1)
    
    # Confirm update
    print(f"Current version: {current_version}")
    print(f"New version:     {new_version}")
    print()
    response = input("Update version? (y/n): ")
    
    if response.lower() == 'y':
        update_version(new_version)
    else:
        print("Cancelled")


if __name__ == "__main__":
    main()

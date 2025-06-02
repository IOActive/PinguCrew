
"""Functions for module management."""

# Do not add any imports to non-standard modules here.
import os
import sys

def fix_module_search_paths(submodule_root=""):
    """Add directories that we must be able to import path."""
    root_directory = os.environ['ROOT_DIR']
    source_directory = os.path.join(root_directory, 'src')

    python_path = os.getenv('PYTHONPATH', '').split(os.pathsep)

    third_party_libraries_directory = os.path.join(root_directory, 'third_party')
    
    if third_party_libraries_directory not in sys.path:
        sys.path.insert(0, third_party_libraries_directory)
        python_path.insert(0, third_party_libraries_directory)

    if source_directory not in sys.path:
        sys.path.insert(0, source_directory)
        python_path.insert(0, source_directory)

    os.environ['PYTHONPATH'] = os.pathsep.join(python_path)

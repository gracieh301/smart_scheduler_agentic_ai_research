"""
Cleanup script to delete generated files after each run.
Removes database files, vector DB, and temporary files.
"""
import os
import shutil
from pathlib import Path

def cleanup():
    """Delete all generated files and directories."""
    
    project_root = Path(__file__).parent
    deleted_items = []
    errors = []
    
    # Files and directories to delete
    items_to_delete = [
        # Database files
        project_root / "backend" / "study_planner.db",
        
        # Vector database directory
        project_root / "backend" / "chroma_db",
        
        # Temporary files
        project_root / "streamlit" / "temp_syllabus.pdf",
        
        # Python cache directories (optional - will regenerate)
        project_root / "backend" / "__pycache__",
        project_root / "backend" / "crew" / "__pycache__",
        project_root / "backend" / "db" / "__pycache__",
        project_root / "backend" / "vector" / "__pycache__",
        project_root / "streamlit" / "__pycache__",
    ]
    
    print("Cleaning up generated files...\n")
    
    for item_path in items_to_delete:
        try:
            if item_path.exists():
                if item_path.is_file():
                    item_path.unlink()
                    deleted_items.append(f"File: {item_path.relative_to(project_root)}")
                    print(f"✓ Deleted: {item_path.relative_to(project_root)}")
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                    deleted_items.append(f"Directory: {item_path.relative_to(project_root)}")
                    print(f"✓ Deleted: {item_path.relative_to(project_root)}")
            else:
                print(f"⊘ Not found: {item_path.relative_to(project_root)}")
        except Exception as e:
            error_msg = f"Error deleting {item_path.relative_to(project_root)}: {e}"
            errors.append(error_msg)
            print(f"✗ {error_msg}")
    
    print(f"\n{'='*50}")
    print(f"Cleanup complete!")
    print(f"Deleted {len(deleted_items)} items")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No errors")

if __name__ == "__main__":
    response = input("This will delete all database files and vector DB. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup()
    else:
        print("Cleanup cancelled.")


#!/usr/bin/env python3
"""
Script to fix all import issues in the backend code.
This replaces all 'from backend.app.' imports with 'from app.' imports.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace all 'from backend.app.' with 'from app.'
        original_content = content
        content = re.sub(r'from backend\.app\.', 'from app.', content)
        
        # Replace all 'import backend.app.' with 'import app.'
        content = re.sub(r'import backend\.app\.', 'import app.', content)
        
        # If content changed, write it back
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def find_and_fix_python_files(directory):
    """Find all Python files and fix their imports."""
    fixed_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and other non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total_count += 1
                
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    return fixed_count, total_count

if __name__ == "__main__":
    backend_dir = "backend"
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory '{backend_dir}' not found!")
        exit(1)
    
    print("🔧 Starting import fix process...")
    print(f"📁 Scanning directory: {backend_dir}")
    
    fixed, total = find_and_fix_python_files(backend_dir)
    
    print("\n" + "="*50)
    print(f"📊 SUMMARY:")
    print(f"   Total Python files: {total}")
    print(f"   Files fixed: {fixed}")
    print(f"   Files unchanged: {total - fixed}")
    print("="*50)
    
    if fixed > 0:
        print("\n🎉 Import fixes completed successfully!")
        print("💡 You can now try starting the backend server.")
    else:
        print("\nℹ️  No import issues found.")

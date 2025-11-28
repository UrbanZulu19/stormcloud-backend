#!/usr/bin/env python3
"""Extract code blocks from agent outputs into actual files"""
import re
import os
from pathlib import Path

def extract_files_from_markdown(md_file, base_path="."):
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Find all === FILE: path === blocks
    pattern = r'===\s*FILE:\s*([^\n]+?)\s*===\s*\n(.*?)(?=\n===\s*FILE:|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    extracted = 0
    for filepath, code in matches:
        filepath = filepath.strip()
        code = code.strip()
        
        # Remove code fences if present
        if code.startswith('```'):
            code = re.sub(r'^```\w*\n', '', code)
            code = re.sub(r'\n```$', '', code)
        
        full_path = Path(base_path) / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(code)
        
        print(f"✅ {filepath}")
        extracted += 1
    
    return extracted

if __name__ == "__main__":
    print("🔍 Extracting code files from agent outputs...")
    print()
    
    total = 0
    for doc in ['02_backend_code.md', '03_docker_code.md', '04_frontend_code.md', 
                '05_deployment_configs.md', '06_documentation.md']:
        doc_path = f"docs/{doc}"
        if os.path.exists(doc_path):
            print(f"📄 {doc}...")
            count = extract_files_from_markdown(doc_path, base_path="..")
            total += count
    
    print()
    print(f"✅ Extracted {total} files")
    
    if total == 0:
        print()
        print("⚠️  Auto-extraction failed. Check docs/*.md and copy manually.")

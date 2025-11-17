#!/usr/bin/env python3
"""
Documentation Navigation Helper
Quickly find relevant documentation for the Epic Web App project.
"""

import os
import glob
import re
from pathlib import Path

def find_docs(query, search_type="content"):
    """
    Search documentation files.
    
    Args:
        query (str): Search term
        search_type (str): "content", "filename", or "path"
    """
    docs_dir = Path(__file__).parent
    results = []
    
    # Get all markdown files
    md_files = glob.glob(str(docs_dir / "**/*.md"), recursive=True)
    
    for file_path in md_files:
        rel_path = Path(file_path).relative_to(docs_dir)
        
        if search_type == "filename":
            if query.lower() in rel_path.name.lower():
                results.append(str(rel_path))
        elif search_type == "path":
            if query.lower() in str(rel_path).lower():
                results.append(str(rel_path))
        else:  # content search
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        results.append(str(rel_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return results

def show_doc_structure():
    """Display the documentation structure."""
    docs_dir = Path(__file__).parent
    
    print("📚 Epic Web App Documentation Structure")
    print("=" * 50)
    
    for item in sorted(docs_dir.rglob("*")):
        if item.is_file() and item.suffix == ".md":
            rel_path = item.relative_to(docs_dir)
            indent = "  " * (len(rel_path.parts) - 1)
            print(f"{indent}📄 {rel_path}")
        elif item.is_dir() and not item.name.startswith("."):
            rel_path = item.relative_to(docs_dir)
            indent = "  " * (len(rel_path.parts) - 1)
            print(f"{indent}📁 {rel_path.name}/")

def search_docs():
    """Interactive search interface."""
    print("\n🔍 Documentation Search")
    print("=" * 30)
    
    while True:
        query = input("\nEnter search term (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        print(f"\nSearching for: '{query}'")
        print("-" * 40)
        
        # Search in content
        content_results = find_docs(query, "content")
        if content_results:
            print(f"📖 Found in content ({len(content_results)} results):")
            for result in content_results[:5]:  # Show first 5
                print(f"  • {result}")
            if len(content_results) > 5:
                print(f"  ... and {len(content_results) - 5} more")
        
        # Search in filenames
        filename_results = find_docs(query, "filename")
        if filename_results:
            print(f"\n📁 Found in filenames ({len(filename_results)} results):")
            for result in filename_results:
                print(f"  • {result}")
        
        # Search in paths
        path_results = find_docs(query, "path")
        if path_results:
            print(f"\n🛣️  Found in paths ({len(path_results)} results):")
            for result in path_results:
                print(f"  • {result}")

def main():
    """Main function."""
    print("🚀 Epic Web App Documentation Navigator")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Show documentation structure")
        print("2. Search documentation")
        print("3. Quick reference")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            show_doc_structure()
        elif choice == "2":
            search_docs()
        elif choice == "3":
            print("\n📚 Quick Reference:")
            print("• AWS Services: docs/aws/README.md")
            print("• S3 Vectors: docs/aws/s3-vectors.md")
            print("• Development: docs/development/README.md")
            print("• Troubleshooting: docs/development/troubleshooting.md")
            print("• Debug Script: backend/debug_s3_vectors.py")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 
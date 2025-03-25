#!/usr/bin/env python3
import sys
import os
import json
import xml.etree.ElementTree as ET
import re

def parse_csproj(project_path):
    """
    Parse .NET project files (.csproj, .vbproj, etc.) and return a JSON
    representation of the project structure.
    """
    if not os.path.exists(project_path):
        return json.dumps({"error": f"File not found: {project_path}"})
    
    try:
        # Get project directory and name
        project_dir = os.path.dirname(project_path)
        project_name = os.path.basename(project_path)
        
        # Parse the project file
        tree = ET.parse(project_path)
        root = tree.getroot()
        
        # Create the root node
        root_node = {
            "id": "root",
            "name": project_name,
            "path": project_name,
            "fullPath": project_path,
            "type": "group",
            "children": []
        }
        
        # Create standard groups
        source_files_node = {
            "id": "source_files",
            "name": "Source Files",
            "path": "source_files",
            "fullPath": project_dir,
            "type": "group",
            "children": []
        }
        
        references_node = {
            "id": "references",
            "name": "References",
            "path": "references",
            "fullPath": None,
            "type": "group",
            "children": []
        }
        
        # Find all source files referenced in the project
        compile_items = []
        content_items = []
        reference_items = []
        
        # Get namespace
        ns = get_namespace(root.tag)
        
        # Process different item types
        # For Compile items (source code)
        for compile_item in root.findall(f".//{ns}Compile") + root.findall(f".//{ns}Content") + root.findall(f".//{ns}None"):
            include_attr = compile_item.get("Include")
            if include_attr:
                file_path = os.path.normpath(os.path.join(project_dir, include_attr))
                if os.path.exists(file_path) and not os.path.isdir(file_path):
                    source_files_node["children"].append({
                        "id": include_attr,
                        "name": os.path.basename(include_attr),
                        "path": include_attr,
                        "fullPath": file_path,
                        "type": "file"
                    })
        
        # For references
        for reference in root.findall(f".//{ns}Reference") + root.findall(f".//{ns}ProjectReference"):
            include_attr = reference.get("Include")
            if include_attr:
                name = include_attr.split(',')[0] if ',' in include_attr else include_attr
                references_node["children"].append({
                    "id": include_attr,
                    "name": name,
                    "path": None,
                    "fullPath": None,
                    "type": "file"
                })
        
        # Add directories not explicitly included in project but existing in the project folder
        directories_to_check = ["Properties", "Models", "Views", "Controllers", "Services", "Data"]
        for dir_name in directories_to_check:
            dir_path = os.path.join(project_dir, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                dir_node = scan_directory(dir_path, dir_name)
                if dir_node and len(dir_node["children"]) > 0:
                    root_node["children"].append(dir_node)
        
        # Add the standard groups if they have children
        if source_files_node["children"]:
            root_node["children"].append(source_files_node)
        
        if references_node["children"]:
            root_node["children"].append(references_node)
        
        # If no source files were found in the project file, scan the directory
        if not source_files_node["children"]:
            scanned_files_node = scan_directory(project_dir, "Source Files", ignore_dirs=directories_to_check)
            if scanned_files_node and scanned_files_node["children"]:
                root_node["children"].append(scanned_files_node)
        
        return json.dumps(root_node)
    
    except Exception as e:
        return json.dumps({"error": f"Error parsing project: {str(e)}"})

def get_namespace(tag):
    """Extract namespace from an XML tag."""
    match = re.match(r'\{(.*?)\}', tag)
    if match:
        return '{' + match.group(1) + '}'
    return ''

def scan_directory(directory_path, name, ignore_dirs=None):
    """Scan a directory and return a node with all files and subdirectories."""
    if ignore_dirs is None:
        ignore_dirs = []
    
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return None
    
    node = {
        "id": name,
        "name": name,
        "path": os.path.basename(directory_path),
        "fullPath": directory_path,
        "type": "group",
        "children": []
    }
    
    try:
        # Get all entries in the directory
        entries = os.listdir(directory_path)
        
        # Sort entries: directories first, then files
        entries.sort(key=lambda x: (0 if os.path.isdir(os.path.join(directory_path, x)) else 1, x.lower()))
        
        for entry in entries:
            # Skip hidden files and directories
            if entry.startswith('.'):
                continue
            
            entry_path = os.path.join(directory_path, entry)
            
            if os.path.isdir(entry_path):
                # Skip directories that we've already processed
                if entry in ignore_dirs:
                    continue
                    
                subdir_node = scan_directory(entry_path, entry)
                if subdir_node and subdir_node["children"]:
                    node["children"].append(subdir_node)
                    
            elif os.path.isfile(entry_path):
                node["children"].append({
                    "id": entry,
                    "name": entry,
                    "path": entry,
                    "fullPath": entry_path,
                    "type": "file"
                })
    
    except Exception as e:
        print(f"Error scanning directory {directory_path}: {e}", file=sys.stderr)
    
    return node

def parse_solution(solution_path):
    """
    Parse Visual Studio .sln file and return a JSON representation
    of the solution structure with all projects.
    """
    if not os.path.exists(solution_path):
        return json.dumps({"error": f"File not found: {solution_path}"})
    
    solution_dir = os.path.dirname(solution_path)
    solution_name = os.path.basename(solution_path)
    
    # Create the root node for the solution
    root_node = {
        "id": "solution",
        "name": solution_name,
        "path": solution_name,
        "fullPath": solution_path,
        "type": "group",
        "children": []
    }
    
    try:
        with open(solution_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Extract project entries from the solution file
        project_pattern = r'Project\("\{[A-F0-9-]+\}"\)\s*=\s*"([^"]+)",\s*"([^"]+)",\s*"\{[A-F0-9-]+\}"'
        projects = re.findall(project_pattern, content)
        
        for project_name, project_path in projects:
            # Convert relative path to absolute
            abs_project_path = os.path.normpath(os.path.join(solution_dir, project_path))
            
            if os.path.exists(abs_project_path):
                # For each project, parse its structure
                if abs_project_path.endswith(('.csproj', '.vbproj')):
                    project_json = parse_csproj(abs_project_path)
                    project_node = json.loads(project_json)
                    if "error" not in project_node:
                        root_node["children"].append(project_node)
                else:
                    # For other project types, just add a simple node
                    project_node = {
                        "id": project_path,
                        "name": project_name,
                        "path": project_path,
                        "fullPath": abs_project_path,
                        "type": "group",
                        "children": scan_directory(os.path.dirname(abs_project_path), project_name)["children"]
                    }
                    root_node["children"].append(project_node)
        
        return json.dumps(root_node)
        
    except Exception as e:
        return json.dumps({"error": f"Error parsing solution: {str(e)}"})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No project file path provided"}))
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if project_path.endswith('.sln'):
        print(parse_solution(project_path))
    elif project_path.endswith(('.csproj', '.vbproj')):
        print(parse_csproj(project_path))
    else:
        print(json.dumps({"error": "Unsupported file type. Please provide a .csproj, .vbproj, or .sln file."})) 
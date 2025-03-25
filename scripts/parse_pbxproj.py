#!/usr/bin/env python3
import sys
import os
import re
import json

def get_project_name(pbxproj_path):
    # Get the .xcodeproj directory name
    xcodeproj_dir = os.path.dirname(pbxproj_path)
    return os.path.basename(xcodeproj_dir).replace('.xcodeproj', '')

def parse_pbxproj(pbxproj_path):
    try:
        with open(pbxproj_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the project name
        project_name = get_project_name(pbxproj_path)
        
        # Create the root node
        root_node = {
            'id': 'root',
            'name': project_name,
            'type': 'group',
            'children': []
        }
        
        # Extract PBXGroup section
        group_section_match = re.search(r'/\* Begin PBXGroup section \*/\s*(.*?)\s*/\* End PBXGroup section \*/', content, re.DOTALL)
        if not group_section_match:
            print("Could not find PBXGroup section", file=sys.stderr)
            sys.exit(1)
        
        group_section = group_section_match.group(1)
        
        # Extract PBXFileReference section
        file_section_match = re.search(r'/\* Begin PBXFileReference section \*/\s*(.*?)\s*/\* End PBXFileReference section \*/', content, re.DOTALL)
        if not file_section_match:
            print("Could not find PBXFileReference section", file=sys.stderr)
            sys.exit(1)
            
        file_section = file_section_match.group(1)
        
        # Find main group (project root)
        project_section_match = re.search(r'/\* Begin PBXProject section \*/\s*(.*?)\s*/\* End PBXProject section \*/', content, re.DOTALL)
        main_group_id = None
        if project_section_match:
            main_group_match = re.search(r'mainGroup\s+=\s+([0-9A-F]{24})', project_section_match.group(1))
            if main_group_match:
                main_group_id = main_group_match.group(1)
        
        if not main_group_id:
            print("Could not find main group", file=sys.stderr)
            sys.exit(1)
        
        # Parse groups
        groups = {}
        group_pattern = re.compile(r'([0-9A-F]{24})\s*/\*\s*(.+?)\s*\*/\s*=\s*\{\s*isa\s*=\s*PBXGroup;\s*(?:children\s*=\s*\(\s*(.*?)\s*\);\s*)?(?:name\s*=\s*(.+?);\s*)?(?:path\s*=\s*(.+?);\s*)?(?:sourceTree\s*=\s*(.+?);\s*)?.*?\};', re.DOTALL)
        
        for match in group_pattern.finditer(group_section):
            group_id = match.group(1)
            group_comment = match.group(2)
            children_str = match.group(3) or ""
            name = match.group(4).strip('"') if match.group(4) else group_comment
            path = match.group(5).strip('"') if match.group(5) else None
            source_tree = match.group(6).strip('"') if match.group(6) else None
            
            # Extract children IDs
            children = []
            if children_str:
                children_matches = re.finditer(r'([0-9A-F]{24})', children_str)
                for child in children_matches:
                    children.append(child.group(1))
            
            groups[group_id] = {
                'id': group_id,
                'name': name,
                'path': path,
                'sourceTree': source_tree,
                'children': children,
                'type': 'group'
            }
        
        # Parse files
        files = {}
        file_pattern = re.compile(r'([0-9A-F]{24})\s*/\*\s*(.+?)\s*\*/\s*=\s*\{\s*isa\s*=\s*PBXFileReference;\s*(?:lastKnownFileType\s*=\s*(.+?);\s*)?(?:name\s*=\s*(.+?);\s*)?(?:path\s*=\s*(.+?);\s*)?(?:sourceTree\s*=\s*(.+?);\s*)?.*?\};', re.DOTALL)
        
        for match in file_pattern.finditer(file_section):
            file_id = match.group(1)
            file_comment = match.group(2)
            file_type = match.group(3)
            name = match.group(4).strip('"') if match.group(4) else None
            path = match.group(5).strip('"') if match.group(5) else file_comment
            source_tree = match.group(6).strip('"') if match.group(6) else None
            
            files[file_id] = {
                'id': file_id,
                'name': name or os.path.basename(path),
                'path': path,
                'type': 'file',
                'sourceTree': source_tree
            }
        
        # Build the tree structure
        project_dir = os.path.dirname(os.path.dirname(pbxproj_path))
        
        def build_tree(node_id, current_path=""):
            if node_id in groups:
                node = groups[node_id].copy()
                node_children = []
                
                # Resolve group path
                if node['sourceTree'] == 'SOURCE_ROOT' and node['path']:
                    node_path = os.path.join(project_dir, node['path'])
                elif node['sourceTree'] == '<group>' and node['path']:
                    node_path = os.path.join(current_path, node['path'])
                else:
                    node_path = current_path
                
                node['fullPath'] = node_path if os.path.exists(node_path) else None
                
                # Process children
                for child_id in node['children']:
                    child_node = build_tree(child_id, node_path)
                    if child_node:
                        node_children.append(child_node)
                
                node['children'] = node_children
                return node if node_children or node['fullPath'] else None
                
            elif node_id in files:
                node = files[node_id].copy()
                
                # Resolve file path
                if node['sourceTree'] == 'SOURCE_ROOT' and node['path']:
                    full_path = os.path.join(project_dir, node['path'])
                elif node['sourceTree'] == '<group>' and node['path']:
                    full_path = os.path.join(current_path, node['path'])
                else:
                    full_path = node['path']
                
                if os.path.exists(full_path):
                    node['fullPath'] = full_path
                    return node
                
            return None
        
        # Build the tree starting from main group
        main_tree = build_tree(main_group_id)
        if main_tree:
            root_node['children'] = main_tree['children']
        
        return root_node
        
    except Exception as e:
        print(f"Error parsing pbxproj: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: parse_pbxproj.py <path_to_project.pbxproj>", file=sys.stderr)
        sys.exit(1)
    
    pbxproj_path = sys.argv[1]
    
    if not os.path.exists(pbxproj_path):
        print(f"Error: File not found: {pbxproj_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        project_structure = parse_pbxproj(pbxproj_path)
        print(json.dumps(project_structure))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main() 
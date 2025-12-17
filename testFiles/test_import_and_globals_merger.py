import ast
import astor  # pip install astor for AST -> code conversion


def extract_imports(tree):
    """
    Extracts all import statements from an AST.
    Returns a list of Import or ImportFrom nodes.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
    return imports


def merge_imports(imports_left, imports_right):
    """
    Merges two lists of import nodes.
    Conflicts: same modules are combined.
    """
    merged = {}

    def add_import(node):
        if isinstance(node, ast.Import):
            for alias in node.names:
                merged[alias.name] = ast.Import(names=[alias])
        elif isinstance(node, ast.ImportFrom):
            key = (node.module, node.level)
            if key not in merged:
                merged[key] = ast.ImportFrom(
                    module=node.module, names=list(node.names), level=node.level
                )
            else:
                # Merge aliases without duplicates
                existing_names = {a.name for a in merged[key].names}
                for a in node.names:
                    if a.name not in existing_names:
                        merged[key].names.append(a)

    for imp in imports_left + imports_right:
        add_import(imp)

    return list(merged.values())


def extract_globals(tree):
    """
    Extracts all top-level assignments (global variables) from an AST.
    """
    globals_list = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            globals_list.append(node)
    return globals_list


def merge_globals(globals_left, globals_right):
    """
    Merges two lists of top-level assignments.
    If the same variable exists, the right-hand side takes precedence.
    """
    merged = {}
    for node in globals_left + globals_right:
        # Only single-target assignments for simplicity
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            merged[var_name] = node
    return list(merged.values())


def replace_top_level(tree, merged_imports, merged_globals):
    """
    Replaces top-level imports and globals with the merged ones.
    Keeps other nodes (like functions, classes) unchanged.
    """
    # Remove existing imports and globals
    new_body = [
        node
        for node in tree.body
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign))
    ]
    # Insert merged imports and globals at the top
    tree.body = merged_imports + merged_globals + new_body
    return tree


# --- Example code Left & Right ---
code_left = """
import os
import sys
from math import sqrt
x = 2
"""

code_right = """
import sys
import json
from math import ceil
y = 5
"""

# Parse ASTs
tree_left = ast.parse(code_left)
tree_right = ast.parse(code_right)

# Extract imports and globals
imports_left = extract_imports(tree_left)
imports_right = extract_imports(tree_right)
globals_left = extract_globals(tree_left)
globals_right = extract_globals(tree_right)

# Merge imports and globals
merged_imports = merge_imports(imports_left, imports_right)
merged_globals = merge_globals(globals_left, globals_right)

# Replace top-level nodes in left AST
merged_tree = replace_top_level(tree_left, merged_imports, merged_globals)

# Convert AST back to code
merged_code = astor.to_source(merged_tree)
print(merged_code)

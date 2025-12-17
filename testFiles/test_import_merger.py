import ast
import astor  # pip install astor für AST -> Code Conversion


def extract_imports(tree):
    """
    Extrahiert alle Import-Statements aus einem AST.
    Gibt eine Liste von Import- oder ImportFrom Nodes zurück.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
    return imports


def merge_imports(imports_left, imports_right):
    """
    Merged zwei Listen von Import-Nodes.
    Konflikte: gleiche Module werden zusammengeführt.
    """
    merged = {}

    # Helper: Import Name -> Node
    def add_import(node):
        if isinstance(node, ast.Import):
            for alias in node.names:
                merged[alias.name] = ast.Import(names=[alias])
        elif isinstance(node, ast.ImportFrom):
            key = (node.module, node.level)
            if key not in merged:
                merged[key] = ast.ImportFrom(
                    module=node.module, names=list(node.names), level=node.level)
            else:
                # Merge Aliase, ohne Duplikate
                existing_names = {a.name for a in merged[key].names}
                for a in node.names:
                    if a.name not in existing_names:
                        merged[key].names.append(a)
    # Hinzufügen aller Imports
    for imp in imports_left + imports_right:
        add_import(imp)

    return list(merged.values())


def replace_imports(tree, merged_imports):
    """
    Entfernt alle alten Imports und fügt die gemergten am Anfang ein.
    """
    # Entferne alte Imports
    new_body = [node for node in tree.body if not isinstance(
        node, (ast.Import, ast.ImportFrom))]
    # Füge gemergte Imports vorne ein
    tree.body = merged_imports + new_body
    return tree


# --- Beispielcode Left & Right ---
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

# AST erstellen
tree_left = ast.parse(code_left)
tree_right = ast.parse(code_right)

# Imports extrahieren
imports_left = extract_imports(tree_left)
imports_right = extract_imports(tree_right)

# Imports mergen
merged_imports = merge_imports(imports_left, imports_right)

# Left AST ersetzen mit gemergten Imports
merged_tree = replace_imports(tree_left, merged_imports)

# Zurück in Code konvertieren
merged_code = astor.to_source(merged_tree)
print(merged_code)

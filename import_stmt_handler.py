import ast


def extract_imports(tree):
    """
    Extrects all import statments from an AST.
    Returns a list of Import or ImportFrom nodes.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
    return imports


def merge_imports(imports_local, imports_remote):
    """
    Merges two lists of import nodes.
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

    for imp in imports_local + imports_remote:
        add_import(imp)
    return list(merged.values())


def replace_top_level(tree, merged_imports):
    """
    Replaces top-level imports with the merged ones.
    Keeps other nodes (like functions, classes) unchanged.
    """
    # Remove existing imports and globals
    new_body = [
        node
        for node in tree.body
        if not isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    # Insert merged imports and globals at the top
    tree.body = merged_imports + new_body
    return tree

import ast
from log_config import logger


def format_nodes_with_lineno(node_or_list):
    """
    Returns node(s) as a string with line numbers.
    Accepts single nodes or a list of nodes.
    """
    if node_or_list is None:
        return ""

    # 1. Normalisierung: Wenn es keine Liste ist, mach eine Liste mit einem Element draus
    nodes = node_or_list if isinstance(node_or_list, list) else [node_or_list]

    lines = []
    for node in nodes:
        # Sicherheitscheck, falls Nicht-AST-Objekte (z.B. Marker) dabei sind
        if isinstance(node, ast.AST):
            lineno = getattr(node, 'lineno', '?')
            code = ast.unparse(node)
            lines.append(f"  Line {lineno}: {code}")
        else:
            # Fallback für Strings oder Marker-Objekte
            lines.append(f"  Line ?: {str(node)}")

    return "\n".join(lines)


def node_to_string(node_or_list):
    """
    Converts AST node(s) into readable code.
    Accepts single nodes or a list of nodes.
    """
    if node_or_list is None:
        return ""

    # 1. Normalisierung: Alles wird zur Liste, damit die Logik gleich bleibt
    nodes = node_or_list if isinstance(node_or_list, list) else [node_or_list]

    code_lines = []
    for node in nodes:
        if isinstance(node, ast.AST):
            code_lines.append(ast.unparse(node))
        else:
            # Fallback für ChangeMarker oder Strings
            code_lines.append(str(node))

    return "\n".join(code_lines)


def analyze_node_types(nodes_left, nodes_right):
    """
    Checks whether the lists contain ONLY constant assignments or functions.
    If not, returns the 'other' nodes.

    Returns:
        is_pure (bool): True if only constant assignments / functions are present.
        map_left (list): List of nodes from left that are not allowed.
        map_right (list): List of nodes from right that are not allowed.
    """
    # Allowed node types
    ALLOWED_TYPES = (
        ast.Assign,
        ast.AnnAssign,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Expr  # but only print statements
    )

    # Lists to store nodes that are NOT allowed
    other_nodes_left = []
    other_nodes_right = []

    # Flag indicating whether all nodes are valid
    all_clean = True

    def is_print_call(node):
        """
        Helper to check if an ast.Expr node is a call to 'print'.
        Structure: Expr -> value=Call -> func=Name(id='print')
        """
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # Check if the function being called is a simple Name (not obj.method())
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == 'print'
        return False

    def is_valid_node(node):
        """
        Checks if a node is allowed:
        ast.Assign,
        ast.AnnAssign,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Expr  # but only print statements
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Assign, ast.AnnAssign)):
            return True
        elif isinstance(node, ast.Expr):
            return is_print_call(node)

        return False

    # 1. Check left nodes
    for node in nodes_left:
        if not is_valid_node(node):
            other_nodes_left.append(node)
            all_clean = False

    # 2. Check right nodes
    for node in nodes_right:
        if not is_valid_node(node):
            other_nodes_right.append(node)
            all_clean = False
    return all_clean, other_nodes_left, other_nodes_right


def is_constant_assignment(node):
    """
    Checks if a node is a constant assignment.
    Examples:
        TIMEOUT = 30        -> True
        DEBUG = True        -> True
        VERSION: str = "1"  -> True
        x = y + 1           -> False
        x: int              -> False (no value)
    """
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        # Check if the value exists and is a constant
        if getattr(node, "value", None) is not None and isinstance(node.value, ast.Constant):
            return True
    return False


def detect_deleted_functions(nodes_base, nodes_local, nodes_remote):
    """
    Ermittelt Funktionen, die in Base vorhanden waren, aber in Local oder Remote gelöscht wurden.

    Returns:
        deleted_in_local (list): Namen der Funktionen, die in Local fehlen.
        deleted_in_remote (list): Namen der Funktionen, die in Remote fehlen.
    """
    # 1. Namen extrahieren (als Set für schnelle Vergleiche)
    names_base = _get_func_names_set(nodes_base)
    names_local = _get_func_names_set(nodes_local)
    names_remote = _get_func_names_set(nodes_remote)

    # 2. Prüfung: Was ist in Base, aber NICHT in Local? (Mengen-Differenz)
    deleted_in_local = list(names_base - names_local)

    # 3. Prüfung: Was ist in Base, aber NICHT in Remote?
    deleted_in_remote = list(names_base - names_remote)

    return deleted_in_local, deleted_in_remote


def _get_func_names_set(nodes):
    """Hilfsfunktion: Gibt ein Set aller Funktionsnamen zurück."""
    if nodes is None:
        return set()

    return {
        node.name
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def is_function_referenced(func_name, nodes):
    """
    Checks if a function name is referenced (used) within a list of AST nodes.

    Args:
        func_name (str): The name of the function to search for (e.g., "calculate_sum").
        nodes (list): A list of AST nodes (e.g., your ChangeSet or merged_sequence).

    Returns:
        bool: True if a reference was found, otherwise False.
    """
    if not nodes:
        return False

    for node in nodes:
        # ast.walk recursively traverses all children of the node
        # (e.g., deep inside If-statements or nested functions)
        for child in ast.walk(node):

            # We look for 'ast.Name' nodes (identifiers for variables or functions)
            if isinstance(child, ast.Name):

                # 1. The name must match the target function name.
                # 2. The context must be 'Load' (meaning: the value is being read/called).
                #    This explicitly excludes assignments (Store) or deletions (Del).
                if child.id == func_name and isinstance(child.ctx, ast.Load):
                    return True

    return False


def find_function_references(func_name, nodes):
    """
    Searches for references to a function and returns their locations and context.

    Args:
        func_name (str): The name of the function to search for.
        nodes (list): A list of AST nodes (e.g., your ChangeSet).

    Returns:
        list: A list of dictionaries. Each dictionary contains:
              - 'lineno': The line number of the match.
              - 'code': The code string of the statement containing the match.
              Returns an empty list [] if no references are found.
    """
    found_refs = []

    if not nodes:
        return found_refs

    for node in nodes:
        # We walk through every statement (node) in the list
        for child in ast.walk(node):

            if isinstance(child, ast.Name):
                # Check for match (Name matches AND it is being loaded/used)
                if child.id == func_name and isinstance(child.ctx, ast.Load):

                    # 1. Get Line Number
                    # We try to get the line number from the parent statement ('node'),
                    # because 'child' (the Name node) sometimes lacks line info in constructed ASTs.
                    lineno = getattr(node, 'lineno', '?')

                    # 2. Get Code Context
                    # We unparse the PARENT node (the statement), so we see "x = my_func()"
                    # instead of just "my_func".
                    try:
                        code_context = ast.unparse(node)
                    except Exception:
                        code_context = "<could not unparse node>"

                    found_refs.append({
                        'lineno': lineno,
                        'code': code_context
                    })

                    # Stop searching in this specific node/statement to avoid
                    # duplicates if the function is called twice in the same line.
                    break

    return found_refs


def log_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read line by line
            for line in f:
                # .rstrip() removes the new line character at the end of the line,
                # because the logger usually adds its own.
                logger.merge(line.rstrip())
    except Exception as e:
        logger.error("Error reading file in log_file_content", e)


def remove_function_by_name_in_mapping(func_name, mapping_changes):
    """
    Removes a function definition (def or async def) from a mapping of change sets.
    Searches in all lists within the dictionary and modifies the specific list in-place.

    Args:
        func_name (str): The name of the function to be removed.
        mapping_changes (dict): A dictionary where keys are IDs and values are lists of AST nodes 
                                (e.g. {1: [node_a, node_b], 2: [node_c]}).

    Returns:
        bool: True if the function was found and removed, False otherwise.
    """
    # Iterate through all change sets (lists) in the mapping
    for change_id, nodes in mapping_changes.items():

        node_to_remove = None

        # Iterate through the nodes in the current list
        for node in nodes:
            # Check for function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    node_to_remove = node
                    break  # Found the node in this list

        # If found in the current list, remove it and stop searching entirely
        if node_to_remove:
            nodes.remove(node_to_remove)
            return True

    return False

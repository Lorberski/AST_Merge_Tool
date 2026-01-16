import ast


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
        ast.AsyncFunctionDef
    )

    # Lists to store nodes that are NOT allowed
    other_nodes_left = []
    other_nodes_right = []

    # Flag indicating whether all nodes are valid
    all_clean = True

    def is_valid_node(node):
        """
        Checks if a node is allowed:
        - FunctionDef / AsyncFunctionDef -> always allowed
        - Assign / AnnAssign -> only allowed if it assigns a constant
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            return is_constant_assignment(node)
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

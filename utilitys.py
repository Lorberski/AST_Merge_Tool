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
    Checks whether the lists contain ONLY  assignments or functions.
    If not, returns the 'other' nodes.
    """

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

    #  Check left nodes
    for node in nodes_left:
        if not is_valid_node(node):
            other_nodes_left.append(node)
            all_clean = False

    #  Check right nodes
    for node in nodes_right:
        if not is_valid_node(node):
            other_nodes_right.append(node)
            all_clean = False
    return all_clean, other_nodes_left, other_nodes_right


def is_constant_assignment(node):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        # Check if the value exists and is a constant
        if getattr(node, "value", None) is not None and isinstance(node.value, ast.Constant):
            return True
    return False


def detect_deleted_functions(nodes_base, nodes_local, nodes_remote):
    
    # extract names
    names_base = _get_func_names_set(nodes_base)
    names_local = _get_func_names_set(nodes_local)
    names_remote = _get_func_names_set(nodes_remote)

    deleted_in_local = list(names_base - names_local)

    deleted_in_remote = list(names_base - names_remote)

    return deleted_in_local, deleted_in_remote


def _get_func_names_set(nodes):
    """returns a set of all function nodes from a List of Nodes"""
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
    """
    if not nodes:
        return False

    for node in nodes:
        for child in ast.walk(node):

            if isinstance(child, ast.Name):

                if child.id == func_name and isinstance(child.ctx, ast.Load):
                    return True

    return False


def find_function_references(func_name, nodes):
    """
    Searches for references to a function and returns their locations and context.
    """
    found_refs = []

    if not nodes:
        return found_refs

    for node in nodes:
        for child in ast.walk(node):

            if isinstance(child, ast.Name):
                if child.id == func_name and isinstance(child.ctx, ast.Load):

        
                    lineno = getattr(node, 'lineno', '?')

                    try:
                        code_context = ast.unparse(node)
                    except Exception:
                        code_context = "<could not unparse node>"

                    found_refs.append({
                        'lineno': lineno,
                        'code': code_context
                    })


                    break

    return found_refs


def remove_function_by_name_in_mapping(func_name, mapping_changes):
    """
    Removes a function definition (def or async def) from a mapping of change sets.
    """
    for change_id, nodes in mapping_changes.items():

        node_to_remove = None

        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    node_to_remove = node
                    break 

        if node_to_remove:
            nodes.remove(node_to_remove)
            return True

    return False


def log_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                logger.merge(line.rstrip())
    except Exception as e:
        logger.error("Error reading file in log_file_content", e)


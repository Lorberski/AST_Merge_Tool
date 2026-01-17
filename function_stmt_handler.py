import ast
from collections import Counter
from log_config import logger
import sys


def attempt_function_merge(node_left, node_right):
    """
    Checks if two nodes are functions with the same name.
    If yes, checks if their bodies can be safely reordered/merged automatically
    based on variable usage and side effects.

    Args:
        node_left (ast.AST): The node from the local branch.
        node_right (ast.AST): The node from the remote branch.

    Returns:
        tuple: (bool, str/list)
            - Success (bool): True if auto-merge is allowed, False if conflict.
            - Result: The merged body (list of nodes) if True, or a reason string if False.
    """

    # 1. Check if both are FunctionDefs (sync or async)
    valid_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    if not isinstance(node_left, valid_types) or not isinstance(node_right, valid_types):
        return False, "Nodes are not both functions."

    # 2. Check if they have the same name
    if node_left.name != node_right.name:
        return False, "Function names do not match."

    logger.debug(f"Analyzing merge safety for function: '{node_left.name}'")

    # 3. Analyze content for safety (Reordering logic)
    # We assume we are checking if the *statements* inside these functions
    # can be merged without conflict.

    # Check LEFT statements
    left_safe = is_safe_for_reordering(node_left.body)
    if not left_safe:
        return False, "Conflict: Local function body contains side effects or complex variable usage."

    # Check RIGHT statements
    right_safe = is_safe_for_reordering(node_right.body)
    if not right_safe:
        return False, "Conflict: Remote function body contains side effects or complex variable usage."

    # 4. Check for variable collisions between the two branches
    # If both define 'x', we cannot simply reorder/merge them automatically.
    if has_variable_collision(node_left.body, node_right.body):
        return False, "Conflict: Variable collision detected between branches."

    # 5. Execute Merge (if safe)
    # Since reordering is allowed, we simply append right changes to left (or vice versa).
    # In a real 3-way merge, you would compare against base to exclude unchanged lines,
    # but here we simply combine the bodies as requested.
    merged_body = node_left.body + node_right.body

    logger.merge(
        f"Auto-merge allowed for function '{node_left.name}' (safe reordering).")
    return True, merged_body


def is_safe_for_reordering(statements):
    """
    Analyzes a list of statements to see if they meet the criteria for automatic reordering.

    Criteria:
    - No side effects (loops, calls, class attrs).
    - Variable patterns: 
        1. Single occurrence (safe).
        2. Declared and used once (safe).
        3. Multiple occurrences > 2 (unsafe).
    """
    var_counter = Counter()

    for stmt in statements:
        # A. Check for Side Effects
        # "Statements with potential side effects (function calls, loops, class attributes)
        # are not automatically reordered"

        # Check for Loops
        for node in ast.walk(stmt):
            if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                logger.debug("-> Unsafe: Loop detected.")
                return False

            # Check for Class Definitions
            if isinstance(node, ast.ClassDef):
                logger.debug("-> Unsafe: Class definition detected.")
                return False

            # Check for Attributes (potential state modification)
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                logger.debug("-> Unsafe: Attribute modification detected.")
                return False

            # Check for Function Calls
            # Note: This is strict. You might want to allow 'print' or pure functions,
            # but the requirement says "calls that may modify state", so we block all to be safe.
            if isinstance(node, ast.Call):
                logger.debug("-> Unsafe: Function call detected.")
                return False

        # B. Collect Variable Usage
        # We count how many times each variable name appears in this block
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name):
                var_counter[node.id] += 1

    # C. Validate Variable Patterns
    for var_name, count in var_counter.items():
        # Case 1: Single occurrence -> Safe
        if count == 1:
            continue

        # Case 2: Declared and used once -> Total 2 -> Safe
        elif count == 2:
            continue

        # Case 3: Multiple occurrences -> Unsafe
        else:
            logger.debug(
                f"-> Unsafe: Variable '{var_name}' appears {count} times (limit is 2).")
            return False

    return True


def has_variable_collision(body_left, body_right):
    """
    Checks if the same variable is modified/used in both branches.
    If 'x' is used in Left and 'x' is used in Right, reordering is risky.
    """
    vars_left = {node.id for stmt in body_left for node in ast.walk(
        stmt) if isinstance(node, ast.Name)}
    vars_right = {node.id for stmt in body_right for node in ast.walk(
        stmt) if isinstance(node, ast.Name)}

    # Intersection check
    common_vars = vars_left.intersection(vars_right)
    if common_vars:
        logger.debug(f"Variable collision on: {common_vars}")
        return True

    return False


def process_and_merge_functions(mapping_left, mapping_right):
    """
    Identifies functions with the same name in both mappings.
    Attempts to merge them using 'attempt_function_merge'.

    If successful:
    1. Keeps the merged function in the mapping with the higher Key/Index (Change ID).
    2. Updates that function's body with the merged content.
    3. Deletes the function from the other mapping.

    Args:
        mapping_left (dict): Mapping {change_id: [nodes]} for Local changes.
        mapping_right (dict): Mapping {change_id: [nodes]} for Remote changes.
    """

    # 1. Helper to build a lookup table: {func_name: {'id': change_id, 'node': node_obj, 'list': parent_list}}
    def build_func_lookup(mapping):
        lookup = {}
        for change_id, node_list in mapping.items():
            for node in node_list:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lookup[node.name] = {
                        'id': change_id,
                        'node': node,
                        'list': node_list  # Store reference to list for easy deletion
                    }
        return lookup

    # 2. Build lookups for O(1) access
    lookup_left = build_func_lookup(mapping_left)
    lookup_right = build_func_lookup(mapping_right)

    # 3. Find common function names
    common_names = set(lookup_left.keys()) & set(lookup_right.keys())

    for name in common_names:
        info_left = lookup_left[name]
        info_right = lookup_right[name]

        node_left = info_left['node']
        node_right = info_right['node']

        # 4. Attempt the merge
        success, result = attempt_function_merge(node_left, node_right)

        if success:
            merged_body = result
            id_left = info_left['id']
            id_right = info_right['id']

            logger.merge(f"Processing merge for '{name}': Left_ID={
                         id_left}, Right_ID={id_right}")

            # 5. Determine which location is "further down" (higher index)
            # We want to keep the function in the mapping that has the higher Change ID.

            # Case A: Left Index is higher (or equal) -> Keep in Left, Delete from Right
            if id_left >= id_right:
                # Update the body of the LEFT node
                node_left.body = merged_body

                # Delete the node from RIGHT mapping
                try:
                    info_right['list'].remove(node_right)
                    logger.merge(
                        f"-> Kept in LEFT (ID {id_left}). Removed from RIGHT (ID {id_right}).")
                except ValueError:
                    logger.debug(f"Could not remove '{
                                 name}' from right (already removed?)")

            # Case B: Right Index is higher -> Keep in Right, Delete from Left
            else:
                # Update the body of the RIGHT node
                node_right.body = merged_body

                # Delete the node from LEFT mapping
                try:
                    info_left['list'].remove(node_left)
                    logger.merge(
                        f"-> Kept in RIGHT (ID {id_right}). Removed from LEFT (ID {id_left}).")
                except ValueError:
                    logger.debug(f"Could not remove '{
                                 name}' from left (already removed?)")

        else:
            # Merge failed (unsafe)
            reason = result
            logger.merge(f"Auto-merge failed for '{name}': {reason}")
            sys.exit(1)
            # Both functions remain in their respective mappings (manual conflict resolution needed later)

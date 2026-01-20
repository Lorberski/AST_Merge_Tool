import ast
from collections import Counter
from log_config import logger
import sys


def attempt_function_merge(node_left, node_right):
    """
    Checks if two nodes are functions with the same name.
    If yes, checks if their bodies can be safely reordered/merged automatically
    based on variable usage and side effects.

    """

    valid_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    if not isinstance(node_left, valid_types) or not isinstance(node_right, valid_types):
        return False, "Nodes are not both functions."
    
    if node_left.name != node_right.name:
        return False, "Function names do not match."

    logger.debug(f"Analyzing merge safety for function: '{node_left.name}'")

    
    # Check LEFT statements
    left_safe = is_safe_for_reordering(node_left.body)
    if not left_safe:
        return False, "Conflict: Local function body contains side effects or complex variable usage."

    # Check RIGHT statements
    right_safe = is_safe_for_reordering(node_right.body)
    if not right_safe:
        return False, "Conflict: Remote function body contains side effects or complex variable usage."

    # Check for variable collisions between the two branches
    
    if has_variable_collision(node_left.body, node_right.body):
        return False, "Conflict: Variable collision detected between branches."

    # Execute Merge (if safe)
    merged_body = node_left.body + node_right.body

    logger.merge(
        f"Auto-merge allowed for function '{node_left.name}' (safe reordering).")
    return True, merged_body


def is_safe_for_reordering(statements):
    """
    Analyzes a list of statements to see if they meet the criteria for automatic reordering.
    """
    var_counter = Counter()

    for stmt in statements:
       
        for node in ast.walk(stmt):
            if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                logger.debug("-> Unsafe: Loop detected.")
                return False

            if isinstance(node, ast.ClassDef):
                logger.debug("-> Unsafe: Class definition detected.")
                return False

            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                logger.debug("-> Unsafe: Attribute modification detected.")
                return False

            if isinstance(node, ast.Call):
                logger.debug("-> Unsafe: Function call detected.")
                return False

        for node in ast.walk(stmt):
            if isinstance(node, ast.Name):
                var_counter[node.id] += 1

    for var_name, count in var_counter.items():
        if count == 1:
            continue

        elif count == 2:
            continue

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
    """

    def build_func_lookup(mapping):
        lookup = {}
        for change_id, node_list in mapping.items():
            for node in node_list:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lookup[node.name] = {
                        'id': change_id,
                        'node': node,
                        'list': node_list 
                    }
        return lookup

    lookup_left = build_func_lookup(mapping_left)
    lookup_right = build_func_lookup(mapping_right)

    # Find common function names
    common_names = set(lookup_left.keys()) & set(lookup_right.keys())

    for name in common_names:
        info_left = lookup_left[name]
        info_right = lookup_right[name]

        node_left = info_left['node']
        node_right = info_right['node']

      
        success, result = attempt_function_merge(node_left, node_right)

        if success:
            merged_body = result
            id_left = info_left['id']
            id_right = info_right['id']

            logger.merge(f"Processing merge for '{name}': Left_ID={
                         id_left}, Right_ID={id_right}")

            # Determine which location is "further down" (higher index)
            
            if id_left >= id_right:
                node_left.body = merged_body

                try:
                    info_right['list'].remove(node_right)
                    logger.merge(
                        f"-> Kept in LEFT (ID {id_left}). Removed from RIGHT (ID {id_right}).")
                except ValueError:
                    logger.debug(f"Could not remove '{
                                 name}' from right (already removed?)")

        
            else:
                
                node_right.body = merged_body

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

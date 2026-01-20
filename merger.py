import import_stmt_handler
from log_config import logger
import ast_mapper
import import_stmt_handler
import ast
import utilitys
import function_stmt_handler as fsh


def merge_imports(local_file_tree, remote_file_tree):
    imports_local_File = import_stmt_handler.extract_imports(local_file_tree)
    imports_remote_File = import_stmt_handler.extract_imports(remote_file_tree)

    merged_imports_list = import_stmt_handler.merge_imports(
        imports_local_File, imports_remote_File)

    return import_stmt_handler.replace_top_level(local_file_tree, merged_imports_list)


class ChangeMarker:
    def __init__(self, change_id):
        self.change_id = change_id

    def __repr__(self):
        return f"<CHANGE_MARKER id={self.change_id}>"


class Merger:
    def __init__(self, ast_base, ast_local, ast_remote):
        self.ast_base = ast_base
        self.ast_local = ast_local
        self.ast_remote = ast_remote

        self.merged_imports_list = self.return_merged_imports()

        self.local_nodes_wo_import = ast_mapper.map_top_level_nodes_without_imports(
            self.ast_local)
        self.remote_nodes_wo_imports = ast_mapper.map_top_level_nodes_without_imports(
            self.ast_remote)
        self.lcs_local_and_remote_wo_imports = ast_mapper.get_lcs_with_difflib(
            self.local_nodes_wo_import, self.remote_nodes_wo_imports)

    def return_merged_imports(self):
        imports_local_File = import_stmt_handler.extract_imports(
            self.ast_local)
        imports_remote_File = import_stmt_handler.extract_imports(
            self.ast_remote)

        merged_imports_list = import_stmt_handler.merge_imports(
            imports_local_File, imports_remote_File)

        return merged_imports_list

    def create_changesets(self):
        """
        Uses the LCS between local and remote as anchors.
        Walks both sequences in sync, collecting gaps before each anchor as changes.
        """
        merged_sequence = []

        lcs_queue = self.lcs_local_and_remote_wo_imports[:]
        local_queue = self.local_nodes_wo_import[:]
        remote_queue = self.remote_nodes_wo_imports[:]

        mapping_changes_left = {}
        mapping_changes_right = {}

        change_id = 0

        while lcs_queue:
           
            anchor = lcs_queue.pop(0)
            diff_nodes_local = []
            while local_queue and not self._are_nodes_equal(local_queue[0], anchor):
                diff_nodes_local.append(local_queue.pop(0))

            if local_queue:
                local_queue.pop(0)

            diff_nodes_remote = []
            while remote_queue and not self._are_nodes_equal(remote_queue[0], anchor):
                diff_nodes_remote.append(remote_queue.pop(0))

            if remote_queue:
                remote_queue.pop(0)

            if diff_nodes_local or diff_nodes_remote:
                mapping_changes_left[change_id] = diff_nodes_local
                mapping_changes_right[change_id] = diff_nodes_remote

                merged_sequence.append(ChangeMarker(change_id))

                change_id += 1

            merged_sequence.append(anchor)

        if local_queue or remote_queue:

            mapping_changes_left[change_id] = list(local_queue)
            mapping_changes_right[change_id] = list(remote_queue)

            merged_sequence.append(ChangeMarker(change_id))

        return merged_sequence, mapping_changes_left, mapping_changes_right

    def merging(self, merged_sequence, mapping_changes_left, mapping_changes_right):
        full_tree_body = []
        auto_merging_possible = True

        # nodes_left and nodes_right are only the change nodes without imports
        nodes_left = [node for node_list in mapping_changes_left.values()
                      for node in node_list]

        nodes_right = [node for node_list in mapping_changes_right.values()
                       for node in node_list]
        collisions = check_assignment_collision(nodes_left, nodes_right)
        if collisions:
            logger.debug("in merger")
            logger.debug("collisons:")
            logger.merge(
                "Auto merging not possible due to conflicting assignments.")

            for var_name in sorted(collisions):
                logger.merge(f"--- Conflict for Variable: '{var_name}' ---")

                # 1. Passende Nodes aus LEFT suchen und formatieren
                left_matches = [
                    n for n in nodes_left if var_name in get_assigned_names(n)]
                left_str = utilitys.format_nodes_with_lineno(left_matches)
                logger.merge("LEFT (Local):")
                for line in left_str.splitlines():
                    logger.merge(line)

                # 2. Passende Nodes aus RIGHT suchen und formatieren
                right_matches = [
                    n for n in nodes_right if var_name in get_assigned_names(n)]
                right_str = utilitys.format_nodes_with_lineno(right_matches)
                logger.merge("RIGHT (Remote):")
                for line in right_str.splitlines():
                    logger.merge(line)

            logger.merge("-------------------------------------------")
            auto_merging_possible = False
        else:
            logger.debug("no assignments conflicts detected")

        all_clean, other_nodes_left, other_nodes_right = utilitys.analyze_node_types(
            nodes_left, nodes_right)

        if all_clean:
            logger.debug(
                "node types OK. Only constant assigments and Functions in the changesets")
        else:
            logger.merge(
                "Auto merging not possible due node types that the merge tool can't handle yet")
            if other_nodes_left:
                logger.merge("Local Nodes that can't be handled:")
                left_str = utilitys.format_nodes_with_lineno(other_nodes_left)
                for line in left_str.splitlines():
                    logger.merge(line)

            if other_nodes_right:
                right_str = utilitys.format_nodes_with_lineno(
                    other_nodes_right)
                logger.merge("Remote Nodes that can't be handled:")
                for line in right_str.splitlines():
                    logger.merge(line)

            auto_merging_possible = False

        if self.merged_imports_list and auto_merging_possible:
            full_tree_body.append(self.merged_imports_list)
            logger.merge("Merged Imports:")
            for line in utilitys.node_to_string(self.merged_imports_list).splitlines():
                logger.merge(line)

        deleted_fun_left, deleted_fun_right = utilitys.detect_deleted_functions(
            ast_mapper.map_top_level_nodes_without_imports(self.ast_base), nodes_left, nodes_right)

        for fun in deleted_fun_left:
            if utilitys.is_function_referenced(fun, nodes_right):
                logger.merge(f"Auto merging not possible. Function '{
                             fun}' was deleted in LEFT (Local), but new references to it were found in RIGHT (Remote)")
                auto_merging_possible = False
                refs = utilitys.find_function_references(fun, nodes_right)
                for ref in refs:
                    logger.merge(f"   -> Line {ref['lineno']}: {ref['code']}")

            else:
                utilitys.remove_function_by_name_in_mapping(
                    fun, mapping_changes_right)
                logger.merge(
                    f"Function '{fun}' was deleted in LEFT (Local). "
                    "No references found in RIGHT (Remote). "
                    "Removed function from merge result (deleted from RIGHT set)."
                )

        for fun in deleted_fun_right:
            if utilitys.is_function_referenced(fun, nodes_left):
                logger.merge(f"Auto merging not possible. Function '{
                             fun}' was deleted in RIGHT (Remote), but new references to it were found in LEFT (Local)")
                auto_merging_possible = False
                refs = utilitys.find_function_references(fun, nodes_left)
                for ref in refs:
                    logger.merge(f"   -> Line {ref['lineno']}: {ref['code']}")

            else:
                utilitys.remove_function_by_name_in_mapping(
                    fun, mapping_changes_left)
                logger.merge(
                    f"Function '{fun}' was deleted in RIGHT (Remote). "
                    "No references found in LEFT (Local). "
                    "Removed function from merge result (deleted from LEFT set)."
                )

        fsh.process_and_merge_functions(
            mapping_changes_left, mapping_changes_right)

        for item in merged_sequence:
            if isinstance(item, ChangeMarker):
                cid = item.change_id
                nodes_l = mapping_changes_left[cid]
                nodes_r = mapping_changes_right[cid]

                if nodes_l and nodes_r and auto_merging_possible:
                    logger.merge("Conflicting nodes:")
                    logger.merge("LEFT (Local):")
                    str_l = utilitys.format_nodes_with_lineno(nodes_l)
                    for line in str_l.splitlines():
                        logger.merge(line)

                    logger.merge("RIGHT (Remote):")
                    str_r = utilitys.format_nodes_with_lineno(nodes_r)
                    for line in str_r.splitlines():
                        logger.merge(line)

                    logger.merge(
                        "Can be merged automatically and will be added to the merge.")

                full_tree_body.append(nodes_l)
                full_tree_body.append(nodes_r)

            else:
                full_tree_body.append(item)

        if auto_merging_possible:
            return full_tree_body
        else:
            return False

    def _are_nodes_equal(self, node1, node2):
        """
        Hilfsfunktion: Vergleicht zwei Nodes inhaltlich.
        Wichtig, da LCS-Node und Remote-Node unterschiedliche Objekte sind.
        """
        if node1 is None or node2 is None:
            return False
        # include_attributes=False ist extrem wichtig, um Zeilennummern zu ignorieren!
        return ast.dump(node1, include_attributes=False) == ast.dump(node2, include_attributes=False)


def get_assigned_names(node):
    """
    Extrahiert die Variablennamen aus einer Zuweisung.
    Gibt ein Set von Namen zurück (z.B. {'x', 'y'} bei x = y = 1).
    """
    found_names = set()

    # Fall 1: Normale Zuweisung (x = 1)
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                found_names.add(target.id)
            # (Optional: Tuple unpacking wie 'x, y = ...' ist komplexer,
            #  hier ignorieren wir es für einfache Konflikterkennung oft)

    # Fall 2: Typisierte Zuweisung (x: int = 1)
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            found_names.add(node.target.id)

    return found_names


def check_assignment_collision(nodes_left, nodes_right):
    """
    Prüft, ob in beiden Listen dieselbe Variable zugewiesen wird.
    Returns:
        collisions: dict
            Schlüssel: Name der kollidierenden Variable
            Wert: dict mit 'left' und 'right', die Listen der Nodes enthalten, die die Variable zuweisen
    """
    # 1. Mapping von Namen zu Nodes erstellen
    mapping_left = {}
    for node in nodes_left:
        for name in get_assigned_names(node):
            mapping_left.setdefault(name, []).append(node)

    mapping_right = {}
    for node in nodes_right:
        for name in get_assigned_names(node):
            mapping_right.setdefault(name, []).append(node)

    # 2. Schnittmenge der Namen bestimmen
    collision_names = set(mapping_left.keys()).intersection(
        mapping_right.keys())

    # 3. Mapping der Kollisions-Nodes erstellen
    collisions = {}
    for name in collision_names:
        collisions[name] = {
            "left": mapping_left[name],
            "right": mapping_right[name]
        }

    return collisions

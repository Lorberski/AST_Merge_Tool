import import_stmt_handler
from log_config import logger
import ast_mapper
import import_stmt_handler
import ast


def merge_imports(local_file_tree, remote_file_tree):
    imports_local_File = import_stmt_handler.extract_imports(local_file_tree)
    imports_remote_File = import_stmt_handler.extract_imports(remote_file_tree)

    merged_imports_list = import_stmt_handler.merge_imports(
        imports_local_File, imports_remote_File)

    return import_stmt_handler.replace_top_level(local_file_tree, merged_imports_list)


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

    def merging(self):
        new_body = []

        # Wir machen Kopien der Listen, damit wir sie destruktiv (pop) bearbeiten können,
        # ohne das Originalobjekt für immer zu leeren (falls du es noch brauchst).
        # Wenn die Listen "verbraucht" werden dürfen, brauchst du das [:] nicht.
        lcs_queue = self.lcs_local_and_remote_wo_imports[:]
        local_queue = self.local_nodes_wo_import[:]
        remote_queue = self.remote_nodes_wo_imports[:]

        mapping_changes_left = {}
        mapping_changes_right = {}

        # Change Set ID (Startet bei 0 oder 1, je nach Geschmack)
        change_id = 0

        while lcs_queue:
            # 1. Den nächsten Anker aus dem LCS holen
            anchor = lcs_queue.pop(0)

            # --- LOCAL ABARBEITEN ---
            diff_nodes_local = []
            # Solange der Kopf von Local NICHT der Anker ist, gehört es zum Diff
            while local_queue and not self._are_nodes_equal(local_queue[0], anchor):
                diff_nodes_local.append(local_queue.pop(0))

            # Den Anker selbst aus Local entfernen (er ist ja processed)
            if local_queue:
                local_queue.pop(0)

            # --- REMOTE ABARBEITEN ---
            diff_nodes_remote = []
            # Solange der Kopf von Remote NICHT der Anker ist...
            while remote_queue and not self._are_nodes_equal(remote_queue[0], anchor):
                diff_nodes_remote.append(remote_queue.pop(0))

            # Den Anker selbst aus Remote entfernen
            if remote_queue:
                remote_queue.pop(0)

            # --- MAPPING SPEICHERN ---
            # Wir speichern nur, wenn es wirklich Änderungen gab (optional)
            # Oder immer, um die IDs synchron zu halten (Besser für Vergleich!)
            if diff_nodes_local or diff_nodes_remote:
                mapping_changes_left[change_id] = diff_nodes_local
                mapping_changes_right[change_id] = diff_nodes_remote
                change_id += 1

            # Optional: Wenn du auch leere "Zwischenräume" zählen willst,
            # entferne das 'if' oben und rücke die Zuweisungen ein.

        # --- REST-NODES (TAIL) ---
        # Nach dem letzten LCS-Node kann noch Code kommen (ganz am Ende der Datei)
        if local_queue or remote_queue:
            mapping_changes_left[change_id] = list(
                local_queue)  # Rest als Liste
            mapping_changes_right[change_id] = list(
                remote_queue)  # Rest als Liste

        return mapping_changes_left, mapping_changes_right

    def _are_nodes_equal(self, node1, node2):
        """
        Hilfsfunktion: Vergleicht zwei Nodes inhaltlich.
        Wichtig, da LCS-Node und Remote-Node unterschiedliche Objekte sind.
        """
        if node1 is None or node2 is None:
            return False
        # include_attributes=False ist extrem wichtig, um Zeilennummern zu ignorieren!
        return ast.dump(node1, include_attributes=False) == ast.dump(node2, include_attributes=False)

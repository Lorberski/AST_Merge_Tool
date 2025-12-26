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

    def merging(self):
        # Die "Sequenz-Liste", die die Struktur der Datei vorgibt
        merged_sequence = []

        # Queues kopieren (wie gehabt)
        lcs_queue = self.lcs_local_and_remote_wo_imports[:]
        local_queue = self.local_nodes_wo_import[:]
        remote_queue = self.remote_nodes_wo_imports[:]

        mapping_changes_left = {}
        mapping_changes_right = {}

        change_id = 0

        while lcs_queue:
            # 1. Den nächsten Anker aus dem LCS holen
            anchor = lcs_queue.pop(0)

            # --- GAP DETECTION (Lücke vor dem Anker suchen) ---

            # Local Diff sammeln
            diff_nodes_local = []
            while local_queue and not self._are_nodes_equal(local_queue[0], anchor):
                diff_nodes_local.append(local_queue.pop(0))

            # Anker aus Local entfernen
            if local_queue:
                local_queue.pop(0)

            # Remote Diff sammeln
            diff_nodes_remote = []
            while remote_queue and not self._are_nodes_equal(remote_queue[0], anchor):
                diff_nodes_remote.append(remote_queue.pop(0))

            # Anker aus Remote entfernen
            if remote_queue:
                remote_queue.pop(0)

            # --- ENTSCHEIDUNG: GAB ES EINE LÜCKE/ÄNDERUNG? ---
            if diff_nodes_local or diff_nodes_remote:
                # A. Mapping speichern
                mapping_changes_left[change_id] = diff_nodes_local
                mapping_changes_right[change_id] = diff_nodes_remote

                # B. Marker in die Sequenz einfügen (VOR dem Anker)
                merged_sequence.append(ChangeMarker(change_id))

                change_id += 1

            # 2. Den unveränderten Anker (LCS Node) in die Sequenz einfügen
            merged_sequence.append(anchor)

        # --- TAIL (Rest nach dem letzten Anker) ---
        if local_queue or remote_queue:
            # Mapping speichern
            mapping_changes_left[change_id] = list(local_queue)
            mapping_changes_right[change_id] = list(remote_queue)

            # Marker ganz ans Ende der Sequenz hängen
            merged_sequence.append(ChangeMarker(change_id))

        # Rückgabe: Die Struktur-Liste UND die Inhalte der Änderungen
        return merged_sequence, mapping_changes_left, mapping_changes_right

    def _are_nodes_equal(self, node1, node2):
        """
        Hilfsfunktion: Vergleicht zwei Nodes inhaltlich.
        Wichtig, da LCS-Node und Remote-Node unterschiedliche Objekte sind.
        """
        if node1 is None or node2 is None:
            return False
        # include_attributes=False ist extrem wichtig, um Zeilennummern zu ignorieren!
        return ast.dump(node1, include_attributes=False) == ast.dump(node2, include_attributes=False)

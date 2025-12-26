import ast


class ConflictDetector:
    def __init__(self, tree_local, tree_remote):
        self.local = tree_local
        self.remote = tree_remote
        self.conflicts = []

    def check_all(self):
        """Führt alle Checks aus und gibt eine Liste von Konflikt-Beschreibungen zurück."""
        self.check_imports()
        self.check_globals()
        self.check_functions()
        return self.conflicts

    def _nodes_differ(self, node1, node2):
        """
        Vergleicht zwei AST-Nodes rein strukturell.
        WICHTIG: include_attributes=False ignoriert Zeilennummern!
        Sonst wäre jede verschobene Funktion ein Konflikt.
        """
        return ast.dump(node1, include_attributes=False) != ast.dump(node2, include_attributes=False)

    def check_imports(self):
        """
        Prüft auf Namenskollisionen bei Imports.
        Konflikt: 'import numpy as np' vs 'import pandas as np' (gleicher Alias, anderes Modul).
        """
        local_imports = self._map_imports(self.local)
        remote_imports = self._map_imports(self.remote)

        # Schnittmenge prüfen
        for name in set(local_imports) & set(remote_imports):
            node_l = local_imports[name]
            node_r = remote_imports[name]

            if self._nodes_differ(node_l, node_r):
                self.conflicts.append({
                    "type": "IMPORT",
                    "name": name,
                    "msg": f"Import alias '{name}' defined differently in both branches."
                })

    def check_globals(self):
        """
        Prüft globale Variablenzuweisungen.
        Konflikt: 'TIMEOUT = 10' vs 'TIMEOUT = 20'.
        """
        local_vars = self._map_globals(self.local)
        remote_vars = self._map_globals(self.remote)

        for name in set(local_vars) & set(remote_vars):
            # Das ist der Value-Node (z.B. Constant(10))
            val_l = local_vars[name]
            val_r = remote_vars[name]

            if self._nodes_differ(val_l, val_r):
                self.conflicts.append({
                    "type": "GLOBAL_VAR",
                    "name": name,
                    "msg": f"Global variable '{name}' has different values."
                })

    def check_functions(self):
        """
        Prüft Funktionen.
        Konflikt: Gleicher Name, aber unterschiedlicher Body/Argumente.
        """
        local_funcs = self._map_functions(self.local)
        remote_funcs = self._map_functions(self.remote)

        for name in set(local_funcs) & set(remote_funcs):
            func_l = local_funcs[name]
            func_r = remote_funcs[name]

            if self._nodes_differ(func_l, func_r):
                self.conflicts.append({
                    "type": "FUNCTION",
                    "name": name,
                    "msg": f"Function '{name}' was modified in both branches differently."
                })

    # --- Helper Mapper ---

    def _map_imports(self, tree):
        """Mapped Alias-Namen auf den Import-Node."""
        mapping = {}
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    # Key ist der Name, unter dem das Modul im Code verfügbar ist
                    key = alias.asname if alias.asname else alias.name
                    mapping[key] = node
        return mapping

    def _map_globals(self, tree):
        """Mapped Variablennamen auf ihren zugewiesenen Wert (Node.value)."""
        mapping = {}
        for node in tree.body:
            # Wir schauen nur auf einfache Zuweisungen: x = ...
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        mapping[target.id] = node.value
        return mapping

    def _map_functions(self, tree):
        """Mapped Funktionsnamen auf den ganzen Funktions-Node."""
        mapping = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                mapping[node.name] = node
        return mapping

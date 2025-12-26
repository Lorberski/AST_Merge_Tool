from log_config import logger
import ast
import difflib


def map_top_level_nodes(ast):
    ordered_nodes = []

    for node in ast.body:
        ordered_nodes.append(node)
        logger.debug(node)

    return ordered_nodes


def map_top_level_nodes_without_imports(tree):
    ordered_nodes = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        ordered_nodes.append(node)
        logger.debug(node)

    return ordered_nodes


class NodeWrapper:
    def __init__(self, node):
        self.node = node
        self._content = ast.dump(node, include_attributes=False)

    def __eq__(self, other):
        return self._content == other._content

    def __hash__(self):
        return hash(self._content)

    def __repr__(self):
        name = getattr(self.node, 'name', getattr(
            self.node, 'id', type(self.node).__name__))
        return f"<{name}>"


def get_lcs_with_difflib(nodes_left, nodes_right):

    if nodes_left is None:
        nodes_left = []
        logger.warning("nodes_left in get_lcs_with_difflib is NONE!!")
    if nodes_right is None:
        nodes_right = []
        logger.warning("nodes_right in get_lcs_with_difflib is NONE!!")

    left_wrapped = [NodeWrapper(n) for n in nodes_left]
    right_wrapped = [NodeWrapper(n) for n in nodes_right]

    matcher = difflib.SequenceMatcher(None, left_wrapped, right_wrapped)

    lcs = []

    try:

        for match in matcher.get_matching_blocks():
            if match.size > 0:
                for k in range(match.size):
                    lcs.append(left_wrapped[match.a + k].node)
        return lcs
    except Exception as e:
        logger.error("Error in get_lcs_with_difflib", e)
        return lcs

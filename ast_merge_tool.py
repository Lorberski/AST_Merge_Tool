#!/usr/bin/env python3

import sys
import parser
import astor
from merger import Merger
import check_syntax
from log_config import logger, multiline_debug_log
import ast_mapper


def main():

    try:
        logger.merge("Starting Mergeing")

        BASE_FILE = sys.argv[1]
        LOCAL_FILE = sys.argv[2]
        REMOTE_FILE = sys.argv[3]
        MERGED_FILE = sys.argv[4]

        logger.merge(f"Starting merge: BASE={BASE_FILE}, LOCAL={
            LOCAL_FILE}, REMOTE={REMOTE_FILE}")

        for file_path in [BASE_FILE, LOCAL_FILE, REMOTE_FILE]:
            if not check_syntax.check_file_syntax(file_path):
                sys.exit(1)

        ast_base = parser.parse_file_to_ast(BASE_FILE)
        ast_local = parser.parse_file_to_ast(LOCAL_FILE)
        ast_remote = parser.parse_file_to_ast(REMOTE_FILE)

        locoal_top_nodes = ast_mapper.map_top_level_nodes(ast_local)
        remote_top_nodes = ast_mapper.map_top_level_nodes(ast_remote)
        logger.debug("LCS TEST:")
        logger.debug("local_top_nodes:")
        logger.debug(locoal_top_nodes)
        # logger.debug("remote_top_nodes:")
        # logger.debug(remote_top_nodes)
        # logger.debug("LCS result:")
        # logger.debug(ast_mapper.get_lcs_with_difflib(
        #   locoal_top_nodes, remote_top_nodes))
        logger.debug("localt_top_nodes without imports:")
        logger.debug(ast_mapper.map_top_level_nodes_without_imports(ast_local))

        logger.debug("BASE FILE:")
        multiline_debug_log(parser.ast_tree_to_String(ast_base))
        logger.debug("-------------------------------------")
        logger.debug("LOCAL FILE:")
        multiline_debug_log(parser.ast_tree_to_String(ast_local))
        logger.debug("REMOTE FILE:")
        logger.debug("-------------------------------------")
        multiline_debug_log(parser.ast_tree_to_String(ast_remote))
        logger.debug("-------------------------------------")

        # merged_tree = merger.merge_imports(ast_local, ast_remote)
        # merged_code = astor.to_source(merged_tree)
        # multiline_debug_log(merged_code)

        logger.debug("test Merge Class:")
        merger = Merger(ast_base, ast_local, ast_remote)

        changsets = merger.merging()
        logger.debug("changset from merging:")
        logger.debug(changsets)

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            f.write("needs to be added")

        sys.exit(0)
        logger.info("MERGE SUCCESSFUL")
    except Exception as e:
        sys.exit(1)
        logger.error("AST Merge Tool failed unexpectedly: ", e)


if __name__ == "__main__":
    main()

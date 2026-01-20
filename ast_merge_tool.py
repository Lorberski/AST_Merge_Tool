#!/usr/bin/env python3

import sys
import parser
import ast
from merger import Merger
import check_syntax
from log_config import logger, multiline_debug_log
import ast_mapper
import autopep8
import utilitys


def main():

    try:
        logger.merge("+------------------------------------+")
        logger.merge("|          STARTING MERGING          |")
        logger.merge("+------------------------------------+")

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
       
        # ------------------------------------ MERGING --------------------------------------------------
        merger = Merger(ast_base, ast_local, ast_remote)

        merged_sequence, mapping_changes_left, mapping_changes_right = merger.create_changesets()

        logger.debug("changeset from merging:")
        logger.debug(merged_sequence)
        logger.debug(mapping_changes_left)
        logger.debug(mapping_changes_right)

        merged_tree = merger.merging(
            merged_sequence,
            mapping_changes_left,
            mapping_changes_right
        )

        # ----------------------------------------------------------------------------------------------

        if not merged_tree:
            logger.merge(
                "Merge process terminated due to conflicts that cannot be resolved automatically by the tool.")
            sys.exit(1)

        raw_code = ast.unparse(merged_tree)
        formatted_code = autopep8.fix_code(raw_code)

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            f.write(formatted_code)
            # test if MERGED_FILE is checked for SyntaxErrors
            # f.write("(")

        if not check_syntax.check_file_syntax(MERGED_FILE):
            logger.error(
                "Automatic merging is not possible due to syntax errors in the merged output.")
            sys.exit(1)

        logger.merge("---------------- MERGE RESULT ---------------------")
        logger.merge("BASE FILE:")
        for line in BASE_FILE.splitlines():
            logger.debug(line)
            utilitys.log_file_content(BASE_FILE)
        logger.merge("-------------------------------------")
        logger.merge("LOCAL FILE:")
        for line in LOCAL_FILE.splitlines():
            logger.debug(line)
            utilitys.log_file_content(LOCAL_FILE)
        logger.merge("-------------------------------------")
        for line in REMOTE_FILE.splitlines():
            logger.debug(line)
            utilitys.log_file_content(REMOTE_FILE)
        logger.merge("-------------------------------------")
        logger.merge("MERGE FILE:")
        for line in formatted_code.splitlines():
            logger.merge(line)
        logger.merge("-------------------------------------")

        logger.merge("[OK] MERGE SUCCESSFUL")
        sys.exit(0)
    
    except Exception as e:
        sys.exit(1)
        logger.error("AST Merge Tool failed unexpectedly: ", e)



if __name__ == "__main__":
    main()

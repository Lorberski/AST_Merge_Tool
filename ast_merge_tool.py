#!/usr/bin/env python3

import sys
import parser
import astor
import merger
import check_syntax
from log_config import logger, multiline_debug_log
import subprocess
import os


def main():

    logger.merge("Starting Mergeing")

    try:
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

        logger.debug("------ AST MERGE TOOL ------")
        logger.debug("BASE FILE:")
        multiline_debug_log(parser.ast_tree_to_String(ast_base))
        logger.debug("-------------------------------------")
        logger.debug("LOCAL FILE:")
        multiline_debug_log(parser.ast_tree_to_String(ast_local))
        logger.debug("-------------------------------------")
        logger.debug("REMOTE FILE:")
        multiline_debug_log(parser.ast_tree_to_String(ast_remote))
        logger.debug("-------------------------------------")

        merged_tree = merger.merge_imports(ast_local, ast_remote)
        merged_code = astor.to_source(merged_tree)
        multiline_debug_log(merged_code)

        with open(MERGED_FILE, "w", encoding="utf-8") as f:
            f.write(merged_code)

        sys.exit(0)
        logger.info("MERGE SUCCESSFUL")
    except Exception as e:
        logger.error("An error occured", e)


if __name__ == "__main__":
    main()

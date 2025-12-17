#!/usr/bin/env python3

import sys
import parser
import astor
import merger


def main():
    BASE_FILE = sys.argv[1]
    LOCAL_FILE = sys.argv[2]
    REMOTE_FILE = sys.argv[3]
    MERGED_FILE = sys.argv[4]

    ast_base = parser.parse_file_to_ast(BASE_FILE)
    ast_local = parser.parse_file_to_ast(LOCAL_FILE)
    ast_remote = parser.parse_file_to_ast(REMOTE_FILE)
    print("------ AST MERGE TOOL ------")
    print("")
    print("BASE FILE:")
    parser.print_ast_tree(ast_base)
    print("-------------------------------------")
    print("LOCAL FILE:")
    parser.print_ast_tree(ast_local)
    print("-------------------------------------")
    print("REMOTE FILE:")
    parser.print_ast_tree(ast_remote)
    print("-------------------------------------")

    merged_tree = merger.merge_imports(ast_local, ast_remote)
    merged_code = astor.to_source(merged_tree)
    print(merged_code)

    with open(MERGED_FILE, "w", encoding="utf-8") as f:
        f.write(merged_code)

    print("Merge OK")

    sys.exit(0)


if __name__ == "__main__":
    main()

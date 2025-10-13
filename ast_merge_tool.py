import sys
import parser


def main():
    BASE_FILE = sys.argv[1]
    LOCAL_FILE = sys.argv[2]
    REMOTE_FILE = sys.argv[3]
    MERGED_FILE = sys.argv[4]

    ast_base = parser.parse_file_to_ast(BASE_FILE)
    parser.print_ast_tree(ast_base)

    sys.exit(1)

    if __name__ == "__main__":
        main()

import parser
import ast

tree = parser.parse_file_to_ast("../ast_testing_repo/test_large_sample.py")

parser.print_ast_tree(tree)

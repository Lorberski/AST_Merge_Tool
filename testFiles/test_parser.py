import parser
import ast

treeC = parser.parse_file_to_ast("../ast_testing_repo/import1_C.py")
treeB = parser.parse_file_to_ast("../ast_testing_repo/import1_B.py")

print("C:")
parser.print_ast_tree(treeC)
print("B:")
parser.print_ast_tree(treeB)

merged_body = treeC.body + treeB.body
print("merged_body:")

merged_code = parser.unparse_ast_tree(merged_body)
print(merged_code)

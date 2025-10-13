import parser
import ast

treeA = parser.parse_file_to_ast("./code_for_testing/import1_A.py")
treeB = parser.parse_file_to_ast("./code_for_testing/import1_B.py")

print("A:")
parser.print_ast_tree(treeA)
print("B:")
parser.print_ast_tree(treeB)

merged_body = treeA.body + treeB.body
print("merged_body:")

merged_code = parser.unparse_ast_tree(merged_body)
print(merged_code)

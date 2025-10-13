import ast


def parse_python_code(code_string):
    try:
        tree = ast.parse(code_string)
        return tree
    except SyntaxError as e:
        print(f"Error parsing code_string: {e}")
        return None


def unparse_python_code(ast_object):
    try:
        code = ast.unparse(ast_object)
        return code
    except SyntaxError as e:
        print(f"Error unparsing ast_object: {e}")
        return None

import ast
import os


def parse_python_code(code_string):
    try:
        tree = ast.parse(code_string)
        return tree
    except SyntaxError as e:
        print(f"Error parsing code_string: {e}")
        return None


def unparse_ast_tree(ast_object):
    try:
        code = ast.unparse(ast_object)
        return code
    except SyntaxError as e:
        print(f"Error unparsing ast_object: {e}")
        return None


def parse_file_to_ast(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        return tree
    except SyntaxError as e:
        # Original: print(f"Syntaxfehler in {file_path}: {e}")
        print(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        # Original: print(f"Ein Fehler ist aufgetreten: {e}")
        print(f"An error occurred: {e}")
        return None


def print_ast_tree(ast_object):
    print(ast.dump(ast_object, indent=4))

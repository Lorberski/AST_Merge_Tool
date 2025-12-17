import import_stmt_handler


def merge_imports(local_file_tree, remote_file_tree):
    imports_local_File = import_stmt_handler.extract_imports(local_file_tree)
    imports_remote_File = import_stmt_handler.extract_imports(remote_file_tree)

    merged_imports_list = import_stmt_handler.merge_imports(
        imports_local_File, imports_remote_File)

    return import_stmt_handler.replace_top_level(local_file_tree, merged_imports_list)

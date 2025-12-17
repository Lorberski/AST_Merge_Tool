from log_config import logger


def check_file_syntax(file_path: str) -> bool:
    """
    Checks a Python file for syntax errors and prints detailed error info.
    Returns True if no syntax errors.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, file_path, "exec")
        logger.info(f"No syntax errors found in {file_path}.")
        return True

    except SyntaxError as e:
        if e:
            logger.error(f"Syntax Error in {file_path}: ", exc_info=True)
        return False

    except Exception as ex:
        if ex:
            logger.error(f"Error checking {file_path}: ", exc_info=True)
        return False

def format_citation(file_path: str, line_number: int) -> str:
    """
    Format as 'file_path:line_number'
    Normalizes path separators to forward slashes for consistency
    Uses format: file_path (line: line_number) to avoid key:value parsing issues
    """
    # Normalize path separators (Windows \ to /)
    normalized_path = file_path.replace('\\', '/')
    # Use format that's less likely to be parsed as key:value
    return f"{normalized_path} (line {line_number})"


import os
import re
from pathlib import Path


# Prohibited characters on Windows & POSIX
INVALID_CHARS_REGEX = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(filename: str, default_name: str = "download_file") -> str:
    """Sanitize an untrusted remote or user-supplied filename.
    
    Prevents path traversal, directory escaping, null bytes, and illegal filesystem characters.
    """
    if not filename or not isinstance(filename, str):
        return default_name

    # Take only the basename (strips any path components)
    clean = os.path.basename(filename.strip())

    # Remove non-ASCII and unprintable characters for cross-platform and Windows console safety
    clean = re.sub(r"[^\x20-\x7E]", "", clean)

    # Replace invalid filesystem characters with an underscore
    clean = INVALID_CHARS_REGEX.sub("_", clean)

    # Remove consecutive underscores or dots
    clean = re.sub(r"_+", "_", clean)
    clean = re.sub(r"^\.+", "", clean)  # Prevent hidden or parent directory names

    # Split name and extension
    stem, ext = os.path.splitext(clean)
    stem = stem.strip(" ._")

    # If stem became empty, use default
    if not stem:
        stem = default_name

    # Ensure safe extension (remove invalid characters)
    if ext:
        ext = INVALID_CHARS_REGEX.sub("", ext).lower()
        if len(ext) > 10:  # Truncate absurdly long extensions
            ext = ext[:10]

    final_name = f"{stem}{ext}"

    # Truncate length to 200 characters to fit well within filesystem limits
    if len(final_name) > 200:
        max_stem_len = 200 - len(ext)
        final_name = f"{stem[:max_stem_len]}{ext}"

    return final_name or default_name


def generate_unique_filename(base_name: str, existing_names: set) -> str:
    """Generate a unique filename by appending an index if collisions exist."""
    name, ext = os.path.splitext(base_name)
    counter = 1
    candidate = base_name
    while candidate in existing_names:
        candidate = f"{name}_{counter}{ext}"
        counter += 1
    return candidate

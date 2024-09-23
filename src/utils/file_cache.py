import functools
import json
import os
from typing import Any, Callable


def file_cache(
    func: Callable[[str], dict[str, Any]]
) -> Callable[[str], dict[str, Any]]:
    """
    Cache results in a file, and use the query input as the key

    functools.wraps makes the returned wrapped function inherit the same
    docstring as the wrapped function
    """

    @functools.wraps(func)
    def new_func(query: str) -> dict[str, Any]:
        """
        If cache file exists, load it from there
        """
        file_path: str = os.path.join("cache", f"{query.replace(' ', '_')}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                line_in_file: str = file.readline()
            deserialized_line: dict[str, Any] = json.loads(line_in_file)
            return deserialized_line
        else:
            results: dict[str, Any] = func(query)
            serialized_results: str = json.dumps(results)
            with open(file_path, "w") as file:
                file.write(serialized_results)
            return results

    return new_func

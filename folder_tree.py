import os
from logging_utils import setup_logger
logger = setup_logger(debug=True)
class FolderTree:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.tree = self.build_tree_structure()

        # Debugging output to verify the structure
        # logger.info("FolderTree initialized with tree structure:", self.tree)

    def build_tree_structure(self):
        """Recursively builds a tree structure starting from the root folder."""
        def recurse_directory(path):
            subfolders = []
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            subfolders.append({
                                "path": entry.path,
                                "is_leaf": False,
                                "folders": recurse_directory(entry.path)
                            })
            except PermissionError:
                logger.info(f"Permission denied: {path}")
            return subfolders

        return {
            "folders": [
                {
                    "path": self.root_dir,
                    "is_leaf": False,
                    "folders": recurse_directory(self.root_dir)
                }
            ]
        }

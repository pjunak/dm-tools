import os
class FolderTree:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.tree = self.build_tree_structure()

        # Debugging output to verify the structure
        # print("FolderTree initialized with tree structure:", self.tree)

    def build_tree_structure(self):
        """Recursively builds a tree structure starting from the root folder."""
        def recurse_directory(path):
            subfolders = []
            try:
                # List all directories in the current path
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            subfolders.append({
                                "path": entry.path,
                                "is_leaf": False,
                                "folders": recurse_directory(entry.path)  # Recurse into subdirectory
                            })
            except PermissionError:
                # Handle the case where the directory can't be accessed
                print(f"Permission denied: {path}")
            return subfolders

        # Build the root folder structure
        return {
            "folders": [
                {
                    "path": self.root_dir,
                    "is_leaf": False,
                    "folders": recurse_directory(self.root_dir)
                }
            ]
        }

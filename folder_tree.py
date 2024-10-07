import os

class FolderTree:
    def __init__(self, root_folder: str) -> None:
        self.root_folder = root_folder
        self.tree = self.build_tree(root_folder)

    def build_tree(self, root_folder: str) -> dict:
        """Recursively build a tree of folders starting from the root folder."""
        tree = {'path': root_folder, 'folders': [], 'is_leaf': False}
        try:
            for entry in os.scandir(root_folder):
                if entry.is_dir():
                    subtree = self.build_tree(entry.path)
                    tree['folders'].append(subtree)
                elif entry.is_file() and entry.name.endswith('.mp3'):
                    tree['is_leaf'] = True
        except Exception as e:
            print(f"Error reading directory {root_folder}: {e}")
        return tree

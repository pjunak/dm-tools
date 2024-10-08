
import os
from logging_utils import log_method_call
from error_handling import ErrorHandler

class FolderTree:
    def __init__(self, root_folder: str) -> None:
        self.root_folder = root_folder
        self.error_handler = ErrorHandler()  # Initialize error handler
        self.tree = self.build_tree(root_folder)

    @log_method_call
    def build_tree(self, root_folder: str) -> dict:
        tree = {'path': root_folder, 'folders': [], 'is_leaf': False}
        try:
            for entry in os.scandir(root_folder):
                if entry.is_dir():
                    subtree = self.build_tree(entry.path)
                    tree['folders'].append(subtree)
                elif entry.is_file() and entry.name.endswith('.mp3'):
                    tree['is_leaf'] = True
        except Exception as e:
            self.error_handler.log_error(f"Error reading directory {root_folder}: {e}")
            print(f"Error reading directory {root_folder}: {e}")
        return tree

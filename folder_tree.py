import os

class FolderTree:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.tree = self.build_tree(root_dir)

    def build_tree(self, current_dir):
        """Recursively builds a tree structure of the directory, identifying leaf folders."""
        if not os.path.isdir(current_dir):
            return None

        tree_structure = {'path': current_dir, 'folders': [], 'is_leaf': False}

        try:
            entries = os.listdir(current_dir)
            subfolders = [entry for entry in entries if os.path.isdir(os.path.join(current_dir, entry))]
            has_mp3_files = any(entry.endswith('.mp3') for entry in entries)

            # Mark as leaf folder if it contains .mp3 files and no subfolders
            if has_mp3_files and not subfolders:
                tree_structure['is_leaf'] = True
            else:
                for folder in subfolders:
                    sub_tree = self.build_tree(os.path.join(current_dir, folder))
                    if sub_tree:
                        tree_structure['folders'].append(sub_tree)
        except Exception as e:
            print(f"Error accessing folder {current_dir}: {e}")

        return tree_structure

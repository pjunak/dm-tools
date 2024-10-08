import os
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class FolderTree:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Folders"])
        self.tree_structure = self.build_tree(self.root_dir)

    def build_tree(self, path):
        root_item = QStandardItem(os.path.basename(path))
        self.add_subfolders(root_item, path)
        self.model.appendRow(root_item)

    def add_subfolders(self, parent_item, path):
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                folder_item = QStandardItem(entry)
                parent_item.appendRow(folder_item)
                self.add_subfolders(folder_item, full_path)

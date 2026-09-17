import json
import os

class SandboxStorage:
    def __init__(self, base_dir=".sandbox"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_state(self, project_name, state):
        path = os.path.join(self.base_dir, f"{project_name}.json")
        with open(path, 'w') as f:
            json.dump(state, f)

    def load_state(self, project_name):
        path = os.path.join(self.base_dir, f"{project_name}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return json.load(f)

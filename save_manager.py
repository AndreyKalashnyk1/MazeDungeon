import json
import os

SAVE_DIR = "saves"

class SaveManager:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)

    def list_saves(self):
        return [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json")]

    def load_save(self, name):
        path = os.path.join(SAVE_DIR, f"{name}.json")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("coins", 0)

            inv = data.setdefault("inventory", {})

            inv.setdefault("potion", 0)
            inv.setdefault("artifact", 0)
            inv.setdefault("armor", 0)
            inv.setdefault("armor_hits", 0)
            inv.setdefault("pig", 0)
            inv.setdefault("shield", 0)
            data.setdefault("max_level", 1)
            return data

    def create_save(self, name):
        data = {
            "name": name,
            "coins": 0,
            "inventory": {
                "potion": 0,
                "artifact": 0,
                "armor": 0,
                "armor_hits": 0,
                "pig": 0,
                "shield": 0,
            },
            "max_level": 1,
        }
        self.save(data)

        return data

    def save(self, data):
        path = os.path.join(SAVE_DIR, f"{data['name']}.json")

        with open(path, "w", encoding="utf-8") as f:

            json.dump(data, f, ensure_ascii=False, indent=4)

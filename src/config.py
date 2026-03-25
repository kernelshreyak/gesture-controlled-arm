import yaml


DEFAULT_CONFIG_PATH = "config.yaml"


def load_config(path=DEFAULT_CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

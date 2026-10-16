import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Defaults: lowest precedence
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# 2. YAML config
yaml_path = Path("config.development.yaml")
if yaml_path.exists():
    with open(yaml_path) as f:
        yaml_config = yaml.safe_load(f) or {}
    config.update(yaml_config)

# 3. .env file
env_file = dotenv_values(".env")

# Alias: NUM_WORKERS means workers
if "NUM_WORKERS" in env_file:
    config["workers"] = env_file["NUM_WORKERS"]

for key, value in env_file.items():
    if key.startswith("APP_"):
        config[key.removeprefix("APP_").lower()] = value

# 4. OS environment variables
for key, value in os.environ.items():
    if key.startswith("APP_"):
        config[key.removeprefix("APP_").lower()] = value


def coerce(key: str, value):
    """Convert every final config value to the required type."""
    value = str(value)

    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return value.strip().lower() in ("true", "1", "yes", "on")

    return value


# 5. CLI/query-parameter overrides: highest precedence
@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        config[key.strip().lower()] = value

    # Coerce AFTER merging every layer.
    final_config = {
        "port": coerce("port", config["port"]),
        "workers": coerce("workers", config["workers"]),
        "debug": coerce("debug", config["debug"]),
        "log_level": coerce("log_level", config["log_level"]),
        "api_key": "****",
    }

    return final_config
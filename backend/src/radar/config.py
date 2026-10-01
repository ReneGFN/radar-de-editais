import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]


def private_root() -> Path:
    base = os.environ.get("RADAR_PRIVATE_ROOT")
    local = os.environ.get("LOCALAPPDATA")
    if not base and not local:
        raise RuntimeError("Defina RADAR_PRIVATE_ROOT fora do Brain/OneDrive.")
    root = Path(base or str(Path(local) / "RadarDeEditais")).resolve()
    brain = PROJECT.parents[1]
    if root.is_relative_to(brain) or "onedrive" in str(root).lower():
        raise ValueError("Dados e credenciais devem ficar fora do Brain/OneDrive")
    return root


def emit_json(path: Path, value) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

from __future__ import annotations
import json
from pathlib import Path
from pcs.generator.character import CharacterConfig
PROJECTS_DIR=Path('projects')
def save_project(config: CharacterConfig, root: Path=PROJECTS_DIR):
    root.mkdir(parents=True,exist_ok=True); file=root/f'{config.seed}_{_slug(config.name)}.json'; config.save(file); return file
def load_projects(root: Path=PROJECTS_DIR):
    if not root.exists(): return []
    rows=[]
    for p in sorted(root.glob('*.json')):
        try: rows.append((p,CharacterConfig.load(p)))
        except (OSError,ValueError,json.JSONDecodeError): continue
    return rows
def _slug(name):
    import re
    return re.sub(r'[^a-z0-9_-]+','_',name.lower()).strip('_') or 'character'
def generate_batch(config: CharacterConfig,count: int):
    from pcs.generator.character import random_variant
    if count<1 or count>100: raise ValueError('Batch size must be between 1 and 100')
    return [random_variant(config,config.seed+i+1) for i in range(count)]

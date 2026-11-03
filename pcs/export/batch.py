from __future__ import annotations
from pathlib import Path
from pcs.generator.character import CharacterConfig
from pcs.projects.manager import generate_batch
from pcs.export.delivery import export_order

def export_batch(config: CharacterConfig,count: int,destination: str|Path):
    root=Path(destination); root.mkdir(parents=True,exist_ok=True); results=[]
    for variant in generate_batch(config,count):
        folder=root/f'{variant.seed}_{variant.palette}'; results.append(export_order(variant,folder))
    return results

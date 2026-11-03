# Procedural Character Studio
Aplicación local en Python + Streamlit para crear personajes de fantasía originales, editables como geometría vectorial y exportables a paquetes comerciales. Todo el dibujo se genera por código, sin APIs ni recursos externos.

## Instalación en Windows 10/11
1. Instala Python 3.10 o posterior (marca **Add Python to PATH**).
2. Extrae el ZIP del proyecto y abre la carpeta `procedural_character_studio` en Visual Studio Code.
3. Ejecuta `install.bat` (crea `.venv` e instala dependencias desde `requirements.txt`).
4. Ejecuta `run.bat`. El navegador abrirá Streamlit en `http://localhost:8501`.
5. Pruebas opcionales: `.venv\Scripts\python.exe -m unittest discover -s tests`.

## Funciones
- Character Studio con nueve paletas, clases, estilos, cabello, accesorios, proporciones y semillas reproducibles.
- Capas SVG editables y grafo de huesos jerárquicos; PNG RGBA con renderizador supersampled local.
- Biblioteca inicial de componentes y punto de registro extensible desde Python.
- Animaciones procedurales idle, breathing, walking, running, jumping, attacking, casting, damage, death y victory.
- Efectos mágicos, fuego, humo, energía, aura, rayos, partículas, explosiones y círculos.
- Exportación de SVG, PNG, tiras/spritesheets, GIF, JSON y pedido ZIP con documentación Godot.
- Guardado y recuperación de configuraciones JSON, variantes por lotes.

## Uso
Edita la configuración en la barra lateral; la vista previa se actualiza al interactuar. Guarda para crear JSON local en `projects/`. En Animation Studio genera una tira de fotogramas. Export Studio incluye descarga PNG transparente y botón **EXPORTAR PEDIDO**; el archivo descargable contiene `character/`, `animations/`, `spritesheets/`, `effects/`, `previews/` y documentación.

El núcleo también se puede utilizar desde Python:
```python
from pcs.generator import CharacterConfig, build_character
from pcs.engine.svg_writer import save_svg
from pcs.export import export_png
config = CharacterConfig(name="Arcane Guardian", palette="violet")
scene = build_character(config)
save_svg(scene, "guardian.svg")
export_png(scene, "guardian.png")
```

## Arquitectura
`pcs/engine` geometría de escena, rasterizador y SVG; `pcs/generator` configuración y construcción procedural; `pcs/library` catálogo/registro; `pcs/animation` poses cíclicas y spritesheets; `pcs/effects` efectos; `pcs/export` formatos y paquete; `pcs/projects` administración/lotes; `pcs/ui` interfaz Streamlit.

## Límites conocidos / experimental
- Ilustración y articulación están orientadas a un personaje demo original (bruja/arcanista). Variantes cambian paleta, peinado y proporciones; armaduras, clases y estilos seleccionables son actualmente variaciones de la base, no bibliotecas anatómicas completamente distintas.
- Las poses son transformaciones 2D por hueso y las animaciones funcionales son una base procedural; el efecto de magia del pedido es un GIF con cambios de semilla/intensidad por fotograma. Efectos avanzados de humo/fuego aún son experimentales.
- El rasterizador genera PNG local; el export SVG es vectorial editable (incluye capas y gradients), pero las transformaciones de hueso solo se serializan para huesos animados explícitamente en la pose.
- La hoja de sprites consolida secuencialmente las animaciones elegidas. La integración Godot se basa en coordenadas JSON; no se genera una escena Godot.
- No se incluye editor de nodos SVG general ni sistema de importación de arte externo. No hay recursos de terceros.

El permiso de uso comercial cubre los assets generados entregados, no la propiedad/licencia del software. Revisa `documentation/asset_license.txt` dentro del paquete.

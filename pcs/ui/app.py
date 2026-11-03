from __future__ import annotations
import json, tempfile
from pathlib import Path
import streamlit as st
from pcs.animation import AnimationClip, default_clips, render_frames, create_spritesheet
from pcs.effects import add_effect
from pcs.engine.raster import render_vector
from pcs.engine.svg_writer import scene_to_svg
from pcs.export import export_order
from pcs.generator import CharacterConfig, PALETTES, build_character, random_variant
from pcs.library import list_components
from pcs.projects.manager import save_project, load_projects, generate_batch
st.set_page_config(page_title='Procedural Character Studio',page_icon='✦',layout='wide')
st.markdown('''<style>.stApp{background:#111019;color:#eee8f5}.block-container{padding-top:1.4rem}.pcs-card{padding:1rem;border:1px solid #382e49;border-radius:14px;background:#1b1824}</style>''',unsafe_allow_html=True)
st.title('✦ Procedural Character Studio')
st.caption('Local vector character design · animation · production exports')
if 'config' not in st.session_state: st.session_state.config=CharacterConfig()
if 'seed' not in st.session_state: st.session_state.seed=st.session_state.config.seed
config=st.session_state.config
with st.sidebar:
    st.header('Character Studio')
    config.name=st.text_input('Nombre',config.name)
    config.character_class=st.selectbox('Clase',['witch','mage','warlock','ranger','knight'],index=['witch','mage','warlock','ranger','knight'].index(config.character_class) if config.character_class in ['witch','mage','warlock','ranger','knight'] else 0)
    config.style=st.selectbox('Estilo',['dark_fantasy','anime_fantasy','semirealistic'])
    config.palette=st.selectbox('Paleta',list(PALETTES),index=list(PALETTES).index(config.palette) if config.palette in PALETTES else 0)
    config.hair=st.selectbox('Cabello',['long_black','short_bob','braided','silver_wave'])
    config.outfit=st.selectbox('Vestimenta',['gothic_dress','battle_robes','light_armor'])
    config.face=st.selectbox('Expresión',['calm','determined','mysterious'])
    config.accessories=st.multiselect('Accesorios',['hat','brooch','skull_brooch'],default=config.accessories)
    config.proportions['head']=st.slider('Proporción de cabeza',.8,1.2,float(config.proportions.get('head',1)),.01)
    config.proportions['shoulders']=st.slider('Ancho de hombros',.8,1.2,float(config.proportions.get('shoulders',1)),.01)
    config.seed=st.number_input('Semilla reproducible',min_value=0,max_value=9999,value=int(config.seed))
    if st.button('🎲 Variante aleatoria',use_container_width=True):
        st.session_state.config=random_variant(config,int(config.seed)+1); st.rerun()
    if st.button('Guardar configuración',use_container_width=True):
        path=save_project(config); st.success(f'Guardado: {path}')

tabs=st.tabs(['Character Studio','Character Library','Animation Studio','Effects Studio','Palette Editor','Export Studio','Projects & Batch'])
scene=build_character(config)
with tabs[0]:
    a,b=st.columns([1,1.1]);
    with a:
        st.subheader(config.name); st.image(render_vector(scene,scale=.75,ss=2),use_container_width=True)
    with b:
        st.markdown('### Componentes vectoriales editables')
        st.write(f'{len(scene.prims)} primitivas · {len(scene.bones)} huesos · semilla `{config.seed}`')
        st.download_button('Descargar SVG editable',scene_to_svg(scene).encode(),file_name='character.svg',mime='image/svg+xml')
        st.download_button('Descargar JSON',json.dumps(config.to_dict(),indent=2).encode(),file_name='character.json',mime='application/json')
with tabs[1]:
    components=list_components(); categories=sorted(set(x.category for x in components)); category=st.selectbox('Categoría',categories)
    st.dataframe([{'ID':c.id,'Componente':c.label,'Descripción':c.description} for c in components if c.category==category],use_container_width=True,hide_index=True)
    st.caption('Registro extensible: añade manifestaciones de componentes mediante pcs.library.add_component sin alterar el motor.')
with tabs[2]:
    clip_name=st.selectbox('Animación',[c.name for c in default_clips()]); c1,c2,c3=st.columns(3)
    fps=c1.slider('FPS',4,30,12); frame_count=c2.slider('Fotogramas',4,36,12); amp=c3.slider('Amplitud',.2,2.0,1.0,.1)
    clip=AnimationClip(clip_name,fps,frame_count,clip_name in ('idle','walking','running','breathing'),amp)
    if st.button('Generar vista previa'):
        frames=render_frames(scene,clip,scale=.42); sheet=create_spritesheet(frames,columns=min(len(frames),6)); st.image(sheet,caption=f'{clip.name}: {frame_count} frames @ {fps} FPS',use_container_width=True)
        import io
        buf=io.BytesIO(); sheet.save(buf,format='PNG'); st.download_button('Descargar spritesheet',buf.getvalue(),file_name=f'{clip.name}.png',mime='image/png')
    st.info('Vista previa por secuencia de frames. Exportaciones incluyen metadatos FPS y coordenadas compatibles con Godot.')
with tabs[3]:
    kind=st.selectbox('Efecto',['magic','fire','smoke','energy','aura','lightning','particles','explosion','circle'])
    col=st.color_picker('Color',PALETTES[config.palette]['magic']); intensity=st.slider('Intensidad',.3,2.0,1.0); count=st.slider('Partículas',4,60,18)
    fx=build_character(config); add_effect(fx,kind,col,intensity,count,config.seed)
    st.image(render_vector(fx,scale=.7,ss=2),caption='Previsualización de efecto procedural',width=360)
with tabs[4]:
    st.subheader('Paletas integradas')
    cols=st.columns(3)
    for i,(name,colors) in enumerate(PALETTES.items()):
        with cols[i%3]:
            swatches=' '.join(f'<span title="{v}" style="display:inline-block;width:25px;height:25px;background:{v};border-radius:5px;margin-right:4px"></span>' for v in colors.values())
            st.markdown(f'**{name}**<br>{swatches}',unsafe_allow_html=True)
    st.caption('Paletas: '+', '.join(PALETTES))
with tabs[5]:
    st.write('Exporta el arte editable, render PNG y pedido con animaciones, hojas de sprites y documentación.')
    if st.button('EXPORTAR PEDIDO',type='primary'):
        with st.spinner('Generando SVG, PNG, animaciones y paquete...'):
            out=Path('deliveries')/f'{config.seed}_{config.name.lower().replace(" ","_")}'; zip_path=export_order(config,out)
        st.success(f'Paquete creado: {zip_path}')
        st.download_button('Descargar ZIP de pedido',zip_path.read_bytes(),file_name=zip_path.name,mime='application/zip')
    import io
    png_buffer=io.BytesIO(); render_vector(scene,scale=1,ss=3).save(png_buffer,format='PNG')
    st.download_button('PNG transparente',png_buffer.getvalue(),file_name='character.png',mime='image/png')
with tabs[6]:
    projects=load_projects()
    if projects:
        selected=st.selectbox('Configuración guardada',[str(p) for p,_ in projects])
        if st.button('Abrir y editar'):
            st.session_state.config=next(c for p,c in projects if str(p)==selected); st.rerun()
    else: st.info('Aún no hay proyectos guardados.')
    batch=st.number_input('Variantes por lote',min_value=1,max_value=50,value=10)
    if st.button('Generar configuraciones de variantes'):
        variants=generate_batch(config,int(batch)); root=Path('projects/batch'); root.mkdir(parents=True,exist_ok=True)
        for item in variants: item.save(root/f'{item.seed}_{item.palette}.json')
        st.success(f'{len(variants)} configuraciones guardadas en {root}')

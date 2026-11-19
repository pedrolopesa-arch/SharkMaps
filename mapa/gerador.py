"""Gerador de mapas interativos com Folium para o SharkMaps.

Regra de arquitetura: este módulo NUNCA importa PySide6, permitindo
testes independentes da interface gráfica.
"""

import html
from typing import Optional
import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd

# Coordenadas centrais aproximadas do litoral de Pernambuco (Recife / Região Metropolitana)
COORDENADAS_PADRAO_PE = [-8.12, -34.90]
ZOOM_PADRAO = 12


def _criar_popup(linha: pd.Series) -> folium.Popup:
    """Gera popup HTML seguro com os detalhes do ponto usando html.escape."""
    nome = html.escape(str(linha.get("nome", "Sem nome")))
    tipo = html.escape(str(linha.get("tipo", "Não informado")))
    data = html.escape(str(linha.get("data", "")))
    especie = html.escape(str(linha.get("especie", "")))
    descricao = html.escape(str(linha.get("descricao", "")))
    fonte = html.escape(str(linha.get("fonte", "")))

    cor_titulo = "#c0392b" if tipo == "incidente" else "#2980b9"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px; font-size: 13px;">
        <h4 style="margin: 0 0 6px 0; color: {cor_titulo};">{nome}</h4>
        <b>Tipo:</b> {tipo}<br>
        <b>Data:</b> {data or 'Não informada'}<br>
        <b>Espécie:</b> {especie or 'Não identificada'}<br>
        <p style="margin: 6px 0;">{descricao}</p>
        <small style="color: #666;"><b>Fonte:</b> {fonte or 'Não informada'}</small>
    </div>
    """
    return folium.Popup(folium.IFrame(html_content, width=250, height=170), max_width=270)


def _obter_icone(tipo: str) -> folium.Icon:
    """Retorna o ícone apropriado para cada categoria de ponto."""
    if tipo == "incidente":
        return folium.Icon(color="red", icon="warning", prefix="fa")
    elif tipo == "posto_salvavidas":
        return folium.Icon(color="blue", icon="life-ring", prefix="fa")
    return folium.Icon(color="green", icon="info-circle", prefix="fa")


def gerar_mapa(
    df: pd.DataFrame,
    mostrar_incidentes: bool = True,
    mostrar_salvavidas: bool = True,
    agrupar: bool = True,
    mapa_calor: bool = False
) -> folium.Map:
    """Gera e retorna um folium.Map com os pontos cadastrados.

    Args:
        df: DataFrame com as colunas tipo, nome, lat, lon, etc.
        mostrar_incidentes: Se True, plota os incidentes.
        mostrar_salvavidas: Se True, plota os postos de salva-vidas.
        agrupar: Se True, utiliza MarkerCluster.
        mapa_calor: Se True, adiciona camada de calor (HeatMap) para incidentes.

    Returns:
        Instância de folium.Map configurada.
    """
    mapa = folium.Map(
        location=COORDENADAS_PADRAO_PE,
        zoom_start=ZOOM_PADRAO,
        tiles="OpenStreetMap"
    )

    if df.empty or "lat" not in df.columns or "lon" not in df.columns:
        return mapa

    # Filtragem por tipo
    tipos_selecionados = []
    if mostrar_incidentes:
        tipos_selecionados.append("incidente")
    if mostrar_salvavidas:
        tipos_selecionados.append("posto_salvavidas")

    df_filtrado = df[df["tipo"].isin(tipos_selecionados)].copy()

    # Camada de calor (opcional)
    if mapa_calor:
        df_calor = df[df["tipo"] == "incidente"]
        pontos_calor = df_calor[["lat", "lon"]].dropna().values.tolist()
        if pontos_calor:
            HeatMap(pontos_calor, radius=15, blur=10).add_to(mapa)

    # Destino dos marcadores (cluster ou mapa direto)
    container = MarkerCluster(name="Pontos Agrupados").add_to(mapa) if agrupar else mapa

    # Adiciona os marcadores
    for _, linha in df_filtrado.iterrows():
        popup = _criar_popup(linha)
        icone = _obter_icone(str(linha.get("tipo", "")))
        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            popup=popup,
            tooltip=html.escape(str(linha.get("nome", ""))),
            icon=icone
        ).add_to(container)

    # Enquadramento automático dos pontos
    if not df_filtrado.empty:
        min_lat, max_lat = df_filtrado["lat"].min(), df_filtrado["lat"].max()
        min_lon, max_lon = df_filtrado["lon"].min(), df_filtrado["lon"].max()
        if pd.notna(min_lat) and pd.notna(min_lon):
            if min_lat == max_lat and min_lon == max_lon:
                mapa.location = [min_lat, min_lon]
            else:
                mapa.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    return mapa

"""Gerador de mapas interativos com Folium para o SharkMaps.

Suporta camadas de incidentes oficiais, postos de salva-vidas,
relatos pendentes (curadoria), camada de áreas de perigo e mapa de calor.
"""

import html
import json
from pathlib import Path
from typing import Optional
import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd

import config

COORDENADAS_PADRAO_PE = [-8.13, -34.90]
ZOOM_PADRAO = 12


def _criar_popup(linha: pd.Series) -> folium.Popup:
    """Gera popup HTML seguro com os detalhes do ponto usando html.escape."""
    reg_id = html.escape(str(linha.get("id", "")))
    nome = html.escape(str(linha.get("nome", "Sem nome")))
    tipo = html.escape(str(linha.get("tipo", "Não informado")))
    data = html.escape(str(linha.get("data", "")))
    especie = html.escape(str(linha.get("especie", "")))
    descricao = html.escape(str(linha.get("descricao", "")))
    fonte = html.escape(str(linha.get("fonte", "")))
    status = html.escape(str(linha.get("status", "oficial")))

    cor_titulo = "#c0392b" if tipo == "incidente" else "#2980b9"
    badge_status = (
        '<span style="background:#27ae60; color:#fff; padding:2px 6px; border-radius:3px; font-size:10px;">OFICIAL</span>'
        if status == "oficial"
        else '<span style="background:#f39c12; color:#fff; padding:2px 6px; border-radius:3px; font-size:10px;">PENDENTE</span>'
    )

    html_content = f"""
    <div style="font-family: Arial, sans-serif; min-width: 240px; font-size: 13px; line-height: 1.4;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:11px; color:#7f8c8d; font-weight:bold;">#{reg_id}</span>
            {badge_status}
        </div>
        <h4 style="margin: 0 0 6px 0; color: {cor_titulo}; font-size: 14px;">{nome}</h4>
        <b>Tipo:</b> {tipo}<br>
        <b>Data:</b> {data or 'Não informada'}<br>
        <b>Espécie:</b> {especie or 'Não identificada'}<br>
        <p style="margin: 6px 0; color:#2c3e50;">{descricao}</p>
        <small style="color: #7f8c8d;"><b>Fonte:</b> {fonte or 'Não informada'}</small>
    </div>
    """
    return folium.Popup(folium.IFrame(html_content, width=260, height=190), max_width=280)


def _obter_icone(tipo: str, status: str = "oficial") -> folium.Icon:
    """Retorna o ícone e cor apropriados para cada categoria e status."""
    if status == "pendente":
        return folium.Icon(color="orange", icon="question", prefix="fa")

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
    mapa_calor: bool = False,
    mostrar_areas_perigo: bool = True,
    apenas_oficiais: bool = True,
    mostrar_pendentes: bool = False,
) -> folium.Map:
    """Gera e retorna um folium.Map configurado para o litoral de Pernambuco."""
    mapa = folium.Map(
        location=COORDENADAS_PADRAO_PE,
        zoom_start=ZOOM_PADRAO,
        tiles="OpenStreetMap"
    )

    # 1. Camada de Áreas de Perigo / Atenção Máxima (GeoJSON)
    if mostrar_areas_perigo and config.AREAS_PERIGO_GEOJSON.is_file():
        try:
            with open(config.AREAS_PERIGO_GEOJSON, "r", encoding="utf-8") as f:
                geo_data = json.load(f)

            def style_perigo(feature):
                return {
                    "fillColor": "#e74c3c",
                    "color": "#c0392b",
                    "weight": 2.5,
                    "fillOpacity": 0.25,
                    "dashArray": "6, 4",
                }

            folium.GeoJson(
                geo_data,
                name="Área de Atenção Máxima (Canal Submarino)",
                style_function=style_perigo,
                tooltip=folium.GeoJsonTooltip(
                    fields=["nome", "classificacao"],
                    aliases=["Zona:", "Grau de Risco:"],
                    localize=True,
                ),
            ).add_to(mapa)
        except Exception as e:
            print(f"Erro ao carregar camada de perigo: {e}")

    if df.empty or "lat" not in df.columns or "lon" not in df.columns:
        return mapa

    df_trabalho = df.copy()

    # Filtro de status: visitante vê apenas 'oficial'
    if apenas_oficiais and not mostrar_pendentes:
        df_trabalho = df_trabalho[df_trabalho["status"] == "oficial"]
    elif not mostrar_pendentes:
        df_trabalho = df_trabalho[df_trabalho["status"] == "oficial"]

    tipos_selecionados = []
    if mostrar_incidentes:
        tipos_selecionados.append("incidente")
    if mostrar_salvavidas:
        tipos_selecionados.append("posto_salvavidas")

    df_filtrado = df_trabalho[df_trabalho["tipo"].isin(tipos_selecionados)].copy()

    # 2. Camada de Calor (HeatMap) para incidentes
    if mapa_calor:
        df_calor = df_filtrado[df_filtrado["tipo"] == "incidente"]
        pontos_calor = df_calor[["lat", "lon"]].dropna().values.tolist()
        if pontos_calor:
            HeatMap(pontos_calor, radius=18, blur=12).add_to(mapa)

    # 3. Marcadores de Pontos
    container = MarkerCluster(name="Pontos Agrupados").add_to(mapa) if agrupar else mapa

    for _, linha in df_filtrado.iterrows():
        popup = _criar_popup(linha)
        icone = _obter_icone(str(linha.get("tipo", "")), str(linha.get("status", "oficial")))
        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            popup=popup,
            tooltip=html.escape(f"{linha.get('id', '')} - {linha.get('nome', '')}"),
            icon=icone,
        ).add_to(container)

    # 4. Enquadramento automático
    if not df_filtrado.empty:
        # Se contiver pontos em Noronha e no Litoral, centraliza no Litoral por padrão
        df_litoral = df_filtrado[df_filtrado["lat"] < -6.0]
        alvo = df_litoral if not df_litoral.empty else df_filtrado
        min_lat, max_lat = alvo["lat"].min(), alvo["lat"].max()
        min_lon, max_lon = alvo["lon"].min(), alvo["lon"].max()
        if pd.notna(min_lat) and pd.notna(min_lon):
            mapa.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    return mapa

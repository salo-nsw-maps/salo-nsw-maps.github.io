#!/usr/bin/env python
#
# Script to make maps 
#
import json

import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from folium_glify_layer import GlifyLayer, Popup, Tooltip
import branca.colormap as cm

tile_width = 2000.0

# setup data
df_sites = gpd.read_file('data/nsw-site-boundaries.gpkg').to_crs('EPSG:4326')
df_sites.Year = df_sites.Year.astype(int)
df_sites = df_sites[['Site' ,'Year', 'geometry']]
all_sites = df_sites.geometry.unary_union.buffer(0.01)

# formations data
df_formations = gpd.read_file('data/nsw-veg-formations-poly.gpkg').to_crs('EPSG:4326')
df_formations = df_formations[df_formations.intersects(all_sites)]
df_formations = df_formations.dissolve(by="class").reset_index()
df_formations.to_file('data/nsw-veg-formations-grouped.fgb', driver='FlatGeobuf')

# get tiles and point counts
df55 = gpd.read_file("data/z55-tiles-density.gpkg")
df56 = gpd.read_file("data/z56-tiles-density.gpkg")

df = pd.concat([df55, df56], ignore_index=True)

df = df[df.intersects(all_sites)]
df['density_int'] = df.density.round().astype(int)
df = df.dissolve(by="density_int").reset_index()
df['index'] = [str(i) for i in range(df.shape[0])]


# df55_tiles = gpd.read_file('data/nsw-z55-index.gpkg').to_crs('EPSG:4326')
# df55_pts = pd.read_csv(
#     "data/z55-tile-points", sep="\t", names=["path", "point_count"]
# )
# df55_pts.point_count = df_pts.point_count.astype(float)
# df55 = pd.merge(df_tiles, df_pts, on='path')
# df55['Site'] = df.path.str.split("/").str.get(6).str.split("-").str.get(0)
# df55['Year'] = df.path.str.split("/").str.get(6).str.split("-").str.get(0).str.extract(r'(\d{4})').astype(int)
# df55['density'] = df.point_count / (tile_width * tile_width)
# df55['index'] = [str(i) for i in range(df55.shape[0])]


# df56 = df56[df56.intersects(all_sites)]
# df56['density_int'] = df56.density.round().astype(int)
# df56 = df56.dissolve(by="density_int").reset_index()
# df56_tiles = gpd.read_file('data/nsw-z56-index.gpkg').to_crs('EPSG:4326')
# df56_pts = pd.read_csv(
#     "data/z56-tile-points", sep="\t", names=["path", "point_count"]
# )
# df56_pts.point_count = df56_pts.point_count.astype(float)
# df56 = pd.merge(df56_tiles, df56_pts, on='path')
# df56['Site'] = df56.path.str.split("/").str.get(6).str.split("-").str.get(0)
# df56['Year'] = df56.path.str.split("/").str.get(6).str.split("-").str.get(0).str.extract(r'(\d{4})').astype(int)
# df56['density'] = df56.point_count / (tile_width * tile_width)
# df56['index'] = [str(i) for i in range(df56.shape[0])]
# df56.to_file("data/z56-tiles-density.gpkg", driver='GPKG')

geo = gpd.GeoSeries(df.set_index('index')['geometry']).to_json()
# geo_55 = gpd.GeoSeries(df55.set_index('index')['geometry']).to_json()
# geo_56 = gpd.GeoSeries(df56.set_index('index')['geometry']).to_json()
geo_sites = gpd.GeoSeries(df_sites.set_index('Site')['geometry']).to_json()

# setup map
m = folium.Map(
    location = [-32.67824334, 150.95007370],
    zoom_start = 6
    tiles = ["CartoDB dark_matter", ""]
)

folium.Choropleth(
    geo_data = geo,
    name = 'Point Density',
    data = df,
    columns = ['index', 'density_int'],
    key_on = 'feature.id',
    fill_color = 'YlGnBu',
    fill_opacity = 1,
    line_opacity = 0,
    legend_name = 'Lidar Point Density (pt/sq m)',
    # smooth_factor=  0
    show = False,
).add_to(m)

# folium.Choropleth(
#     geo_data = geo_55,
#     name = 'Zone 55 Point Density',
#     data = df55,
#     columns = ['index', 'density_int'],
#     key_on = 'feature.id',
#     fill_color = 'BuPu',
#     fill_opacity = 1,
#     line_opacity = 0,
#     legend_name = 'Z55 Lidar Point Density (pt/sq m)',
#     # smooth_factor=  0,
#     show = False,
# ).add_to(m)

# folium.Choropleth(
#     geo_data = geo_56,
#     name = 'Zone 56 Point Density',
#     data = df56,
#     columns = ['index', 'density_int'],
#     key_on = 'feature.id',
#     fill_color = 'YlGnBu',
#     fill_opacity = 1,
#     line_opacity = 0,
#     legend_name = 'Z56 Lidar Point Density (pt/sq m)',
#     # smooth_factor=  0
#     show = False,
# ).add_to(m)

folium.Choropleth(
    geo_data = geo_sites,
    name = 'Collection Year',
    data = df_sites,
    columns = ['Site','Year'],
    key_on = 'feature.id',
    fill_color = 'Blues',
    fill_opacity = 1,
    line_opacity = 0,
    legend_name = 'Collection Year',
    smooth_factor=  0
).add_to(m)

tooltip = GeoJsonTooltip(
    fields=["Site", "Year"],
    aliases=["Site:", "Year:"],
    localize=True,
    sticky=False,
    labels=True,
    style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
    max_width=800,
)

folium.GeoJson(
    df_sites.to_json(),
    style_function=lambda x: {
        "fillColor": "transparent",
        "color": "black",
        "weight": 2,
        "opacity": 0.4
    },
    tooltip=tooltip,
    zoom_on_click=True,
    name='Sites',
).add_to(m)

m.add_child(folium.map.LayerControl(collapsed=False))

m.save('nsw-points-years.html')

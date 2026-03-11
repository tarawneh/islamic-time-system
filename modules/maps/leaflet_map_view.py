# ============================================================================
# File Name   : leaflet_map_view.py
# Version     : 0.7.2
# Author      : Dr. Rami Tarawneh
# Company     : 7th Layer
# Project     : Islamic Time System
# Description : Interactive Leaflet map widget based on QWebEngineView. Renders
#               semi-transparent rectangular cells that cover the computed grid.
# License     : GNU General Public License v3.0 or later
# ============================================================================
from __future__ import annotations

import json
from PySide6.QtWebEngineWidgets import QWebEngineView


class LeafletMapView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHtml(self._build_html({"type": "FeatureCollection", "features": []}, "osm"))

    def render_feature_collection(self, feature_collection, basemap="osm"):
        self.setHtml(self._build_html(feature_collection, basemap))

    def _build_html(self, feature_collection, basemap):
        feature_json = json.dumps(feature_collection, ensure_ascii=False)
        if basemap in ("satellite", "hybrid"):
            tile_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution = "&copy; Esri"
        else:
            tile_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution = "&copy; OpenStreetMap contributors"

        return """<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
html, body, #map {height:100%; width:100%; margin:0; padding:0;}
.legend {background:white; padding:8px; line-height:1.6; border-radius:6px; border:1px solid #999; direction:rtl;}
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map', {zoomControl:true}).setView([20,20], 2);
L.tileLayer('""" + tile_url + """', {maxZoom:18, attribution:'""" + attribution + """'}).addTo(map);
const data = """ + feature_json + """;

function colorForCategory(c){
    if (c === 'Visible') return '#2e7d32';
    if (c === 'Optical Aid') return '#f9a825';
    if (c === 'Not Visible') return '#c62828';
    if (c === 'Above limit') return '#1565c0';
    if (c === 'Below limit') return '#6d4c41';
    return '#9e9e9e';
}

L.geoJSON(data, {
    style: function(feature){
        return {
            color: colorForCategory(feature.properties.category),
            weight: 0.25,
            opacity: 0.55,
            fillColor: colorForCategory(feature.properties.category),
            fillOpacity: 0.32
        };
    },
    onEachFeature: function(feature, layer){
        const p = feature.properties || {};
        const popup = [
            '<b>المعيار:</b> ' + (p.criterion || ''),
            '<b>الفئة:</b> ' + (p.category || ''),
            '<b>القيمة:</b> ' + (p.raw_value ?? ''),
            '<b>خط العرض:</b> ' + (p.lat ?? ''),
            '<b>خط الطول:</b> ' + (p.lon ?? ''),
            '<b>الدقة:</b> ' + (p.resolution_deg ?? '')
        ].join('<br/>');
        layer.bindPopup(popup);
    }
}).addTo(map);

const legend = L.control({position:'bottomleft'});
legend.onAdd = function(){
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<b>شرح الألوان</b><br>' +
                    '<span style="color:#2e7d32;">■</span> مرئي<br>' +
                    '<span style="color:#f9a825;">■</span> مرئي بمساعدة بصرية<br>' +
                    '<span style="color:#c62828;">■</span> غير مرئي<br>' +
                    '<span style="color:#1565c0;">■</span> فوق الحد<br>' +
                    '<span style="color:#6d4c41;">■</span> تحت الحد<br>' +
                    '<span style="color:#9e9e9e;">■</span> غير محدد';
    return div;
};
legend.addTo(map);
</script>
</body>
</html>"""

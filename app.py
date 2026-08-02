import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timezone, timedelta
import math

# Configuración de la página
st.set_page_config(page_title="Waze de Auroras", page_icon="🌌", layout="wide")

st.title("🌌 Waze de Auroras Global v19.0 (Streamlit Edition)")
st.markdown("Encuentra el mejor claro oscuro para tu 4x4 en tiempo real.")

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
OWM_API_KEY = "5a69f1d6a0399c5c5d56dd66e1bd3bf9"
HAPI_BASE_URL = "https://imag-data.bgs.ac.uk/GIN_V1/hapi"

# ==========================================
# 📡 FUNCIÓN PARA OBTENER DATOS (Se ejecuta al pulsar el botón)
# ==========================================
@st.cache_data(ttl=600) # Guarda en caché durante 10 minutos para no saturar las APIs
def obtener_todos_los_datos():
    # 1. Magnetómetros HAPI
    magnetometros = {
        'SOD': {'nombre': 'Sodankylä', 'coords': [67.37, 26.63]},
        'KIR': {'nombre': 'Kiruna', 'coords': [67.85, 20.42]},
        'ABK': {'nombre': 'Abisko', 'coords': [68.36, 18.82]},
        'NUR': {'nombre': 'Nurmijärvi', 'coords': [60.50, 24.65]}
    }
    
    for codigo in magnetometros:
        try:
            dataset = f"{codigo}/reported/PT1M/native"
            params = {
                'dataset': dataset, 'parameters': 'Field_Vector',
                'start': (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'stop': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            resp = requests.get(f"{HAPI_BASE_URL}/data", params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data and len(data['data']) > 1:
                    valores_z = [punto[1][2] if len(punto[1]) > 2 else 0 for punto in data['data']]
                    perturbacion = abs(valores_z[-1] - valores_z[0])
                    magnetometros[codigo]['activo'] = perturbacion > 50
                    magnetometros[codigo]['perturbacion'] = perturbacion
                else:
                    magnetometros[codigo]['activo'] = False
                    magnetometros[codigo]['perturbacion'] = 0
        except:
            magnetometros[codigo]['activo'] = False
            magnetometros[codigo]['perturbacion'] = 0

    # 2. Kp NOAA
    kp_actual = 0.0
    try:
        resp = requests.get("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", timeout=10)
        if resp.status_code == 200:
            kp_actual = resp.json()[-1].get('kp_index', 0)
    except:
        pass

    return magnetometros, kp_actual

# ==========================================
# 🎛️ INTERFAZ DE USUARIO
# ==========================================
col1, col2 = st.columns([3, 1])

with col2:
    st.metric(label="Kp Index Actual", value="...", key="kp_metric")
    if st.button("🔄 Actualizar Datos en Tiempo Real", type="primary", use_container_width=True):
        st.cache_data.clear() # Borra caché para forzar nueva consulta
        st.rerun()

# Obtener datos
magnetometros, kp_actual = obtener_todos_los_datos()
st.session_state.kp_metric = kp_actual # Actualiza el métrico

# ==========================================
# 🗺️ BASE DE DATOS DE PUNTOS
# ==========================================
base_datos_puntos = [
    {"lat": 68.4500, "lon": 27.6000, "tipo": "🌲 Pista - Lago Lappajärvi"},
    {"lat": 68.5500, "lon": 27.8000, "tipo": "🌲 Pista - Bosque Hammastunturi"},
    {"lat": 68.7500, "lon": 28.1000, "tipo": "🌲 Pista - Nellim (Lago Inari)"},
    {"lat": 68.8000, "lon": 28.5000, "tipo": "🌲 Pista - Frontera Rusa"},
    {"lat": 68.9500, "lon": 26.8000, "tipo": "🌲 Pista - Lago Paatsjoki"},
    {"lat": 68.4231, "lon": 27.4381, "tipo": "🔭 Mirador Kaunispää"},
    {"lat": 68.6558, "lon": 27.5401, "tipo": "🏠 Ivalo Centro"},
    {"lat": 68.9000, "lon": 27.0000, "tipo": "🛣️ E75 - Inari"},
    {"lat": 69.9000, "lon": 27.0000, "tipo": "🛣️ E75 - Utsjoki"},
]

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

focos_luz = [{"nombre": "Ivalo", "coords": [68.6558, 27.5401]}, {"nombre": "Inari", "coords": [69.0744, 27.0278]}]

resultados = []
for punto in base_datos_puntos:
    dist_min_magnet, magnet_cercano, perturbacion_max = float('inf'), None, 0
    for codigo, mag in magnetometros.items():
        dist = calcular_distancia_km(punto['lat'], punto['lon'], mag['coords'][0], mag['coords'][1])
        if dist < dist_min_magnet:
            dist_min_magnet, magnet_cercano = dist, codigo
            perturbacion_max = mag.get('perturbacion', 0)
    
    score_magnet = max(0, 100 - (dist_min_magnet / 150 * 100)) if dist_min_magnet < 150 else 0
    if perturbacion_max > 50: score_magnet *= 1.5
    
    # Simulación de nubosidad (reemplazar con llamada real a OWM si la API está activa)
    nubosidad = 25 # Valor de ejemplo. Descomenta la llamada real abajo si funciona.
    # try:
    #     resp_owm = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={punto['lat']}&lon={punto['lon']}&appid={OWM_API_KEY}&units=metric", timeout=5)
    #     if resp_owm.status_code == 200: nubosidad = resp_owm.json()['clouds'].get('all', 50)
    # except: pass
    
    score_nubes = 100 - nubosidad
    prob_aurora = min(100, (kp_actual * 15) + ((punto['lat'] - 60) / 10 * 10))
    
    dist_a_ciudad = min([calcular_distancia_km(punto['lat'], punto['lon'], c['coords'][0], c['coords'][1]) for c in focos_luz])
    score_luz = max(20, min(100, (dist_a_ciudad - 5) * 5))
    
    score_final = (score_magnet * 0.25 + score_nubes * 0.35 + prob_aurora * 0.25 + score_luz * 0.15)
    
    resultados.append({
        'tipo': punto['tipo'], 'lat': punto['lat'], 'lon': punto['lon'],
        'score': round(score_final, 1), 'magnet_nombre': magnetometros[magnet_cercano]['nombre'],
        'dist_magnet': round(dist_min_magnet, 1), 'perturbacion': round(perturbacion_max, 1),
        'nubosidad': nubosidad, 'prob_aurora': round(prob_aurora, 1), 'score_luz': round(score_luz, 1),
        'dist_ciudad': round(dist_a_ciudad, 1)
    })

resultados.sort(key=lambda x: x['score'], reverse=True)

# Mostrar Top 3 en la barra lateral
with col1:
    st.subheader("🏆 Top 3 Zonas Recomendadas AHORA")
    for i, r in enumerate(resultados[:3]):
        color_nubes = "🟢" if r['nubosidad'] < 30 else "🟡" if r['nubosidad'] < 70 else "🔴"
        st.markdown(f"**{i+1}. {r['tipo']}** (Score: **{r['score']}**)")
        st.markdown(f"   {color_nubes} Nubes: {r['nubosidad']}% | 🌌 Aurora: {r['prob_aurora']}% | 🌑 Luz: {r['score_luz']}/100")
        st.markdown(f"   📡 {r['magnet_nombre']} ({r['dist_magnet']}km) | ⚡ {r['perturbacion']} nT")
        st.markdown(f"   [🚗 Abrir en Waze](https://waze.com/ul?ll={r['lat']},{r['lon']}&navigate=yes) | [🗺️ Google Maps](https://www.google.com/maps/dir/?api=1&destination={r['lat']},{r['lon']})")
        st.divider()

# ==========================================
# 🗺️ MAPA
# ==========================================
mapa = folium.Map(location=[68.5, 26.0], zoom_start=6, tiles="CartoDB DarkMatter")

folium.raster_layers.TileLayer(
    tiles=f"https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
    attr="OpenWeatherMap", name="☁️ Nubes", overlay=True, opacity=0.50
).add_to(mapa)

try:
    folium.GeoJson(
        "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json",
        name="🌈 Óvalo Aurora", overlay=True,
        style_function=lambda f: {"fillColor": "#ff00ff" if f['properties'].get('probability', 0) >= 80 else "#0000ff", "color": "transparent", "fillOpacity": 0.40}
    ).add_to(mapa)
except:
    pass

for i, r in enumerate(resultados):
    color = "green" if i < 3 else "orange" if i < 6 else "blue"
    icono = "tree-conifer" if 'Pista' in r['tipo'] else "star" if i < 3 else "info-sign"
    
    html = f"""
    <div style="width:260px; font-family:Arial; background:#1a1a2e; color:#fff; padding:12px; border-radius:8px;">
        <h4 style="margin:0 0 8px 0; color:#2ecc71;">{r['tipo']}</h4>
        <p style="margin:2px 0; font-size:13px;"><b>Score:</b> {r['score']}/100</p>
        <p style="margin:2px 0; font-size:13px;"><b>☁️ Nubes:</b> {r['nubosidad']}% | <b>🌡️ Prob:</b> {r['prob_aurora']}%</p>
        <p style="margin:2px 0; font-size:13px;"><b>🌑 Cielo Oscuro:</b> {r['score_luz']}/100</p>
        <div style="margin-top:10px; display:flex; gap:5px;">
            <a href="https://waze.com/ul?ll={r['lat']},{r['lon']}&navigate=yes" target="_blank" style="flex:1; background:#33CCFF; color:#000; padding:8px; text-decoration:none; border-radius:5px; text-align:center; font-weight:bold; font-size:12px;">🚗 WAZE</a>
            <a href="https://www.google.com/maps/dir/?api=1&destination={r['lat']},{r['lon']}" target="_blank" style="flex:1; background:#25D366; color:#fff; padding:8px; text-decoration:none; border-radius:5px; text-align:center; font-weight:bold; font-size:12px;">🗺️ GPS</a>
        </div>
    </div>
    """
    folium.Marker(location=[r['lat'], r['lon']], popup=folium.Popup(html, max_width=280), icon=folium.Icon(color=color, icon=icono, prefix='fa')).add_to(mapa)

# Renderizar el mapa en Streamlit
st_folium(mapa, width=1200, height=600)

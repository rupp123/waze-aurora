from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
import requests
import json
from datetime import datetime, timezone, timedelta
import math

VERSION_APP = "1.0.0"

class WazeAurorasApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datos_cache = None
        
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.15, 1)
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        titulo = Label(
            text='🌌 Waze Auroras Pro',
            font_size=dp(20),
            bold=True,
            halign='center'
        )
        version_label = Label(
            text=f'v{VERSION_APP}',
            font_size=dp(12),
            size_hint=(0.3, 1)
        )
        header.add_widget(titulo)
        header.add_widget(version_label)
        self.layout.add_widget(header)
        
        # Botón actualizar
        self.btn_actualizar = Button(
            text='🔄 Actualizar Datos',
            size_hint=(1, 0.08),
            font_size=dp(16),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.btn_actualizar.bind(on_press=self.actualizar_datos)
        self.layout.add_widget(self.btn_actualizar)
        
        # Botón verificar actualizaciones
        self.btn_update = Button(
            text='🔍 Verificar Actualizaciones',
            size_hint=(1, 0.06),
            font_size=dp(14),
            background_color=(0.8, 0.6, 0, 1)
        )
        self.btn_update.bind(on_press=self.verificar_actualizacion)
        self.layout.add_widget(self.btn_update)
        
        # Info Kp
        self.lbl_kp = Label(
            text='Kp: -- | Última: --',
            size_hint=(1, 0.06),
            font_size=dp(14),
            bold=True,
            color=(0, 1, 0, 1)
        )
        self.layout.add_widget(self.lbl_kp)
        
        # Resultados
        scroll = ScrollView(size_hint=(1, 0.7))
        self.resultados_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(500),
            spacing=dp(5)
        )
        scroll.add_widget(self.resultados_layout)
        self.layout.add_widget(scroll)
        
        # Auto-actualizar cada 10 min
        Clock.schedule_interval(self.auto_actualizar, 600)
        
        # Verificar actualizaciones al iniciar
        Clock.schedule_once(lambda dt: self.verificar_actualizacion(None), 2)
        
        # Primera carga
        Clock.schedule_once(lambda dt: self.actualizar_datos(None), 1)
        
        return self.layout
    
    def verificar_actualizacion(self, instance):
        if instance:
            self.btn_update.text = '⏳ Buscando...'
        
        try:
            resp = requests.get(
                "https://raw.githubusercontent.com/rupp123/waze-aurora/main/version.json",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                version_remota = data.get('version', '0.0.0')
                changelog = data.get('changelog', '')
                
                if self.comparar_versiones(version_remota) > 0:
                    self.mostrar_actualizacion(version_remota, changelog)
                else:
                    if instance:
                        self.btn_update.text = '✅ Versión Actualizada'
                        Clock.schedule_once(lambda dt: setattr(self.btn_update, 'text', '🔍 Verificar Actualizaciones'), 2)
        except Exception as e:
            if instance:
                self.btn_update.text = '❌ Error verificación'
                Clock.schedule_once(lambda dt: setattr(self.btn_update, 'text', '🔍 Verificar Actualizaciones'), 2)
    
    def comparar_versiones(self, version_remota):
        v_local = list(map(int, VERSION_APP.split('.')))
        v_remota = list(map(int, version_remota.split('.')))
        
        for i in range(3):
            if v_remota[i] > v_local[i]:
                return 1
            elif v_remota[i] < v_local[i]:
                return -1
        return 0
    
    def mostrar_actualizacion(self, version, changelog):
        self.btn_update.text = ' UPDATE DISPONIBLE'
        self.btn_update.background_color = (1, 0.3, 0, 1)
        
        popup_layout = BoxLayout(orientation='vertical', padding=dp(20))
        popup_layout.add_widget(Label(
            text=f'🎉 Nueva versión {version} disponible!',
            font_size=dp(18),
            bold=True,
            color=(0, 1, 0, 1),
            size_hint=(1, 0.3)
        ))
        popup_layout.add_widget(Label(
            text=f'Cambios:\n{changelog}',
            font_size=dp(14),
            size_hint=(1, 0.5)
        ))
        
        btn_descargar = Button(
            text=' Descargar APK Actualizada',
            size_hint=(1, 0.2),
            background_color=(0, 0.8, 0, 1)
        )
        btn_descargar.bind(on_press=self.abrir_github)
        popup_layout.add_widget(btn_descargar)
        
        self.layout.add_widget(popup_layout)
    
    def abrir_github(self, instance):
        import webbrowser
        webbrowser.open('https://github.com/rupp123/waze-aurora/releases')
    
    def auto_actualizar(self, dt):
        self.actualizar_datos(None)
    
    def actualizar_datos(self, instance):
        if instance:
            self.btn_actualizar.text = '⏳ Cargando...'
        
        try:
            resp = requests.get(
                "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
                timeout=10
            )
            kp_actual = resp.json()[-1].get('kp_index', 0) if resp.status_code == 200 else 0
            
            puntos = [
                {"nombre": "Ivalo Centro", "lat": 68.6558, "lon": 27.5401},
                {"nombre": "Inari Lago", "lat": 68.9061, "lon": 27.0278},
                {"nombre": "Saariselkä", "lat": 68.4231, "lon": 27.4381},
                {"nombre": "Nellim", "lat": 68.8512, "lon": 28.3114},
                {"nombre": "Utsjoki", "lat": 69.9089, "lon": 27.0214},
            ]
            
            self.resultados_layout.clear_widgets()
            
            header = Label(
                text=f'Kp: {kp_actual} | {datetime.now().strftime("%H:%M")}',
                size_hint=(1, None),
                height=dp(40),
                bold=True,
                color=(0, 1, 0, 1),
                font_size=dp(16)
            )
            self.resultados_layout.add_widget(header)
            
            for i, punto in enumerate(puntos):
                prob_aurora = min(100, kp_actual * 15)
                score = prob_aurora
                
                color = (0, 1, 0, 1) if score > 60 else (1, 1, 0, 1)
                
                item = Label(
                    text=f'{i+1}. {punto["nombre"]}\nScore: {score}/100',
                    size_hint=(1, None),
                    height=dp(60),
                    color=color,
                    halign='center',
                    valign='middle',
                    font_size=dp(14)
                )
                item.bind(size=item.setter('text_size'))
                self.resultados_layout.add_widget(item)
                
                btn_waze = Button(
                    text=f'🚗 Navegar - {punto["nombre"]}',
                    size_hint=(1, None),
                    height=dp(45),
                    background_color=(0.2, 0.8, 1, 1),
                    font_size=dp(14)
                )
                
                lat, lon = punto["lat"], punto["lon"]
                waze_url = f'https://waze.com/ul?ll={lat},{lon}&navigate=yes'
                
                btn_waze.bind(on_press=lambda x, url=waze_url: self.abrir_waze(url))
                self.resultados_layout.add_widget(btn_waze)
            
            self.lbl_kp.text = f'Kp: {kp_actual} | Última: {datetime.now().strftime("%H:%M")}'
            
        except Exception as e:
            error_label = Label(
                text=f'Error: {str(e)}',
                size_hint=(1, None),
                height=dp(40),
                color=(1, 0, 0, 1)
            )
            self.resultados_layout.add_widget(error_label)
        
        finally:
            self.btn_actualizar.text = '🔄 Actualizar Datos'
    
    def abrir_waze(self, url):
        import webbrowser
        webbrowser.open(url)

if __name__ == '__main__':
    WazeAurorasApp().run()
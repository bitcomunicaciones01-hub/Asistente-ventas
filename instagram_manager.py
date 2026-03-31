import os
import time
import random
import json
import logging
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv
from agent_logic import sales_agent

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramManager:
    def __init__(self):
        self.cl = Client()
        self.session_file = "ig_session.json"
        self.username = os.getenv("IG_USERNAME")
        self.password = os.getenv("IG_PASSWORD")
        
        # Configuración anti-detección
        self.setup_client_safety()

    def setup_client_safety(self):
        """Configura el cliente con medidas para parecer un dispositivo humano REAL."""
        # 1. Delays aleatorios entre acciones
        self.cl.delay_range = [2, 6]
        
        # 2. Rotación de User Agents (Simula dispositivos móviles reales)
        user_agents = [
            "Instagram 282.0.0.22.119 Android (31/12; 480dpi; 1080x2400; Google; Pixel 6; oriole; qcom; en_US; 475829103)",
            "Instagram 281.0.0.20.105 Android (30/11; 420dpi; 1080x2260; samsung; SM-G973F; beyond1; exynos9820; es_AR; 469210345)",
            "Instagram 280.0.0.15.115 Android (29/10; 440dpi; 1080x2160; Xiaomi; Mi A3; laurel_sprout; qcom; pt_BR; 455209341)",
        ]
        self.cl.set_user_agent(random.choice(user_agents))
        
        # 3. Datos de dispositivo (Simulando un Pixel 6 por defecto)
        self.cl.set_device({
            "app_version": "282.0.0.22.119",
            "android_version": 31,
            "android_release": "12",
            "dpi": "480dpi",
            "resolution": "1080x2400",
            "manufacturer": "Google",
            "device": "Pixel 6",
            "model": "oriole",
            "cpu": "qcom",
            "version_code": "475829103"
        })
        logger.info("[IG] Medidas anti-detección configuradas.")

    def login(self):
        """Login seguro con persistencia de sesión (Local y Railway)."""
        import base64
        import tempfile
        try:
            # 1. Intentar cargar desde variable de entorno (Modo Railway)
            session_b64 = os.getenv("INSTAGRAM_SESSION_B64")
            if session_b64:
                logger.info("[IG] Cargando sesión desde variable de entorno (Railway)...")
                session_data = json.loads(base64.b64decode(session_b64).decode())
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(session_data, tmp)
                    tmp_path = tmp.name
                self.cl.load_settings(tmp_path)
                os.unlink(tmp_path)
            # 2. Intentar cargar desde archivo local
            elif os.path.exists(self.session_file):
                logger.info("[IG] Cargando sesión persistente local...")
                self.cl.load_settings(self.session_file)
            
            logger.info(f"[IG] Conectando como {self.username}...")
            self.cl.login(self.username, self.password)
            
            # Guardamos localmente siempre para tener el backup
            self.cl.dump_settings(self.session_file)
            logger.info("[OK] Conexión exitosa.")
            return True
            
        except Exception as e:
            logger.error(f"[IG] Error en login: {e}")
            return False

    def simulate_human(self):
        """Realiza acciones aleatorias para 'engañar' al algoritmo de Instagram."""
        try:
            logger.info("[IG] Simulando actividad humana...")
            actions = [
                lambda: self.cl.get_timeline_feed(), # Ver feed
                lambda: self.cl.user_info_by_username(self.username), # Ver perfil propio
                lambda: time.sleep(random.uniform(5, 15)) # Simplemente esperar
            ]
            random.choice(actions)()
            logger.info("[IG] Actividad simulada con éxito.")
        except:
            pass

    def monitor_dms(self):
        """Bucle principal de monitoreo de mensajes."""
        logger.info("[IG] Monitoreo de DMs activado.")
        
        # Contador para disparar actividades humanas aleatorias
        activity_counter = 0

        while True:
            try:
                # Cada 5 ciclos de chequeo, simulamos ser humanos
                activity_counter += 1
                if activity_counter >= 5:
                    self.simulate_human()
                    activity_counter = 0

                # Obtenemos hilos no leídos
                threads = self.cl.direct_threads(amount=10, selected_filter="unread")
                
                for thread in threads:
                    messages = thread.messages
                    if not messages: continue
                    
                    last_msg = messages[0]
                    if last_msg.item_type == 'text' and last_msg.user_id != self.cl.user_id:
                        logger.info(f"[IG] Nuevo DM de {thread.thread_title}: {last_msg.text}")
                        
                        # 1. Tiempo de lectura
                        time.sleep(random.uniform(4, 10))
                        
                        # 2. IA genera respuesta
                        response_data = sales_agent.process_message(last_msg.text, context="instagram")
                        response_text = response_data["text"]
                        
                        # 3. Tiempo de escritura
                        writing_time = len(response_text) / 12
                        time.sleep(min(writing_time, 8)) 
                        
                        # 4. Responder
                        self.cl.direct_answer(thread.id, response_text)
                        logger.info(f"[IG] Respondido a {thread.thread_title}")
                
                # Espera entre chequeos (Aleatoria para no ser patrón de bot)
                wait_time = random.uniform(40, 100)
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"[IG] Error en el loop: {e}")
                time.sleep(300)

def run_instagram_bot():
    ig = InstagramManager()
    if ig.username and ig.password:
        if ig.login():
            ig.monitor_dms()
    else:
        logger.error("[IG] Faltan credenciales en .env")

if __name__ == "__main__":
    run_instagram_bot()

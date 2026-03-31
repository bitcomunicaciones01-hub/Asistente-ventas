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
            logger.info(f"[IG-DEBUG] Iniciando proceso de login para usuario: {self.username}")
            if not self.username or not self.password:
                logger.error("[IG-FATAL] No se encontraron IG_USERNAME o IG_PASSWORD en las variables de entorno.")
                return False

            # 1. Intentar cargar desde variable de entorno (Modo Railway)
            session_b64 = os.getenv("INSTAGRAM_SESSION_B64")
            if session_b64:
                logger.info("[IG-DEBUG] Intentando cargar sesión desde INSTAGRAM_SESSION_B64...")
                try:
                    session_data = json.loads(base64.b64decode(session_b64).decode())
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                        json.dump(session_data, tmp)
                        tmp_path = tmp.name
                    self.cl.load_settings(tmp_path)
                    os.unlink(tmp_path)
                    logger.info("[IG-DEBUG] Sesión B64 cargada exitosamente.")
                except Exception as b64e:
                    logger.warning(f"[IG-DEBUG] Error al cargar sesión B64 (ignorando): {b64e}")

            # 2. Intentar cargar desde archivo local
            elif os.path.exists(self.session_file):
                logger.info("[IG-DEBUG] Cargando sesión persistente local (ig_session.json)...")
                self.cl.load_settings(self.session_file)
            
            logger.info(f"[IG-DEBUG] Intentando cl.login() para {self.username}...")
            try:
                self.cl.login(self.username, self.password)
            except Exception as login_err:
                logger.warning(f"[IG-DEBUG] Error en cl.login (reintentando con sesión): {login_err}")
            
            # Recuperar el ID de cualquier forma posible
            try:
                self.my_user_id = str(self.cl.user_id)
            except:
                logger.info("[IG-DEBUG] Buscando User ID manualmente...")
                self.my_user_id = str(self.cl.user_id_from_username(self.username))
            
            logger.info(f"[IG-DEBUG] Logueado con ID de Cuenta: {self.my_user_id}")
            
            # Guardamos localmente siempre para tener el backup
            self.cl.dump_settings(self.session_file)
            logger.info("[OK] Conexión a Instagram establecida correctamente.")
            return True
            
        except Exception as e:
            logger.error(f"[IG-ERROR] Falló el login: {e}")
            if "ChallengeRequired" in str(e) or "checkpoint" in str(e).lower():
                logger.error("[IG-FATAL] Instagram DETECTÓ el inicio de sesión y pide verificación (CHECKPOINT).")
                logger.error("[IG-HELP] Por favor, entrá a tu Instagram desde el celu y marcá 'SÍ, FUI YO'. Después reiniciá el servicio en Railway.")
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
        print("\n" + "="*50)
        print("🚀 [IG-VERSION] v12.4 - BOT FUNCIONANDO Y ACTUALIZADO")
        print("   -> ARREGLO DE BUCLES ACTIVADO")
        print("="*50 + "\n")
        logger.info("[IG-READY] El bot está ONLINE y buscando mensajes no leídos...")
        
        # Contador para disparar actividades humanas aleatorias
        activity_counter = 0

        while True:
            try:
                # Cada 5 ciclos de chequeo, simulamos ser humanos
                activity_counter += 1
                if activity_counter >= 5:
                    self.simulate_human()
                    activity_counter = 0

                # Obtenemos hilos: Principal (No leídos) + Solicitudes (Pending)
                logger.debug("[IG-DEBUG] Consultando bandejas...")
                
                all_threads = []

                # 1. Intentar Bandeja principal
                try:
                    unread_threads = self.cl.direct_threads(amount=20, selected_filter="unread")
                    all_threads.extend(unread_threads)
                except Exception as te:
                    logger.warning(f"[IG-DEBUG] Error al leer inbox principal (posible cambio de Instagram): {te}")
                
                # 2. Intentar Solicitudes (Pending)
                try:
                    pending_threads = self.cl.direct_pending_inbox(amount=10)
                    all_threads.extend(pending_threads)
                except Exception as pe:
                    logger.warning(f"[IG-DEBUG] Error al leer solicitudes pending: {pe}")
                
                if not all_threads:
                    logger.debug("[IG-DEBUG] No hay mensajes nuevos procesables.")

                for thread in all_threads:
                    try:
                        messages = thread.messages
                        if not messages: continue
                        
                        last_msg = messages[0]
                        # IGNORAR si el mensaje es nuestro (evita bucles)
                        is_self = str(last_msg.user_id) == self.my_user_id
                        
                        if last_msg.item_type == 'text' and not is_self:
                            logger.info(f"[IG-EVENTO] Nuevo mensaje en '{thread.thread_title}': '{last_msg.text}'")
                            
                            # 1. Tiempo de lectura
                            delay = random.uniform(3, 7)
                            logger.info(f"[IG-DEBUG] Simulando lectura ({delay:.1f}s)...")
                            time.sleep(delay)
                            
                            # 2. IA genera respuesta
                            logger.info(f"[IG-DEBUG] Consultando al Agente de Ventas...")
                            response_data = sales_agent.process_message(last_msg.text, context="instagram")
                            response_text = response_data["text"]
                            
                            # 3. Tiempo de escritura
                            writing_time = min(len(response_text) / 10, 6)
                            logger.info(f"[IG-DEBUG] Simulando escritura ({writing_time:.1f}s)...")
                            time.sleep(writing_time) 
                            
                            # 4. Responder
                            self.cl.direct_answer(thread.id, response_text)
                            logger.info(f"[IG-OK] Respondido exitosamente a {thread.thread_title}")
                    except Exception as th_err:
                        logger.error(f"[IG-ERROR] Error al procesar hilo individual: {th_err}")
                
                # Espera entre chequeos (Acortada para testing inicial)
                wait_time = random.uniform(20, 50)
                logger.debug(f"[IG-DEBUG] Esperando {wait_time:.1f}s para el próximo chequeo...")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"[IG-ERROR] Error en el loop de monitoreo: {e}")
                time.sleep(120) # Si falla, esperar 2 minutos

def run_instagram_bot():
    ig = InstagramManager()
    if ig.username and ig.password:
        if ig.login():
            ig.monitor_dms()
    else:
        logger.error("[IG] Faltan credenciales en .env")

if __name__ == "__main__":
    run_instagram_bot()

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
        print("🚀 [IG-VERSION] v12.9 - BYPASS MANUAL ACTIVADO")
        print("   -> LEYENDO SOLICITUDES DIRECTAMENTE")
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

                # Obtenemos hilos: Bypass Manual TOTAL (Principal + Solicitudes)
                logger.info("[IG-DEBUG] Consultando bandejas (v13.2)...")
                
                all_threads_data = []

                # 1. Bypass Manual: Bandeja Principal (Inbox)
                try:
                    res_inbox = self.cl.private_request("direct_v2/inbox/", params={"selected_filter": "unread"})
                    if res_inbox.get("status") == "ok":
                        inbox = res_inbox.get("inbox", {})
                        threads = inbox.get("threads", [])
                        logger.info(f"[IG-DEBUG] Inbox Principal: {len(threads)} hilos no leídos encontrados.")
                        for t in threads:
                            items = t.get("items", [])
                            if items:
                                last_msg = items[0]
                                all_threads_data.append({
                                    "id": t.get("thread_id"),
                                    "title": t.get("thread_title", "Chat"),
                                    "text": last_msg.get("text", ""),
                                    "user_id": str(last_msg.get("user_id"))
                                })
                except Exception as ie:
                    logger.warning(f"[IG-DEBUG] Error en bypass de Inbox: {ie}")
                
                # 2. Bypass Manual: Solicitudes (Pending)
                try:
                    res_pend = self.cl.private_request("direct_v2/pending_inbox/")
                    if res_pend.get("status") == "ok":
                        # DIAGNÓSTICO: Ver qué hay adentro si threads está vacío
                        inbox_p = res_pend.get("inbox", {})
                        threads_p = res_pend.get("inbox", {}).get("threads", [])
                        
                        logger.info(f"[IG-DEBUG] Solicitudes (Pending): {len(threads_p)} hilos encontrados.")
                        if not threads_p:
                            logger.info(f"[IG-DEBUG] Campos en respuesta Pending: {res_pend.keys()}")
                            if "inbox" in res_pend:
                                logger.info(f"[IG-DEBUG] Campos en 'inbox': {res_pend['inbox'].keys()}")
                        
                        for tp in threads_p:
                            items_p = tp.get("items", [])
                            if items_p:
                                last_msg_p = items_p[0]
                                all_threads_data.append({
                                    "id": tp.get("thread_id"),
                                    "title": tp.get("thread_title", "Solicitud"),
                                    "text": last_msg_p.get("text", ""),
                                    "user_id": str(last_msg_p.get("user_id"))
                                })
                except Exception as pe:
                    logger.warning(f"[IG-DEBUG] Error en bypass de Pending: {pe}")
                
                if not all_threads_data:
                    logger.debug("[IG-DEBUG] No hay mensajes nuevos procesables.")

                for td in all_threads_data:
                    try:
                        # IGNORAR si el mensaje es nuestro (evita bucles)
                        is_self = td["user_id"] == self.my_user_id
                        
                        if td["text"] and not is_self:
                            logger.info(f"[IG-EVENTO] Nuevo mensaje en '{td['title']}': '{td['text']}'")
                            
                            # 1. Tiempo de lectura
                            delay = random.uniform(3, 7)
                            logger.info(f"[IG-DEBUG] Simulando lectura ({delay:.1f}s)...")
                            time.sleep(delay)
                            
                            # 2. IA genera respuesta
                            logger.info(f"[IG-DEBUG] Consultando al Agente de Ventas...")
                            response_data = sales_agent.process_message(td["text"], context="instagram")
                            response_text = response_data["text"]
                            
                            # 3. Tiempo de escritura
                            writing_time = min(len(response_text) / 10, 6)
                            logger.info(f"[IG-DEBUG] Simulando escritura ({writing_time:.1f}s)...")
                            time.sleep(writing_time) 
                            
                            # 4. Responder
                            try:
                                # Si es una solicitud (Bypass Manual), la aprobamos primero
                                self.cl.direct_thread_approve(td["id"])
                            except:
                                pass # Si ya estaba aprobada o falla, seguimos adelante
                                
                            self.cl.direct_answer(td["id"], response_text)
                            logger.info(f"[IG-OK] Respondido exitosamente a {td['title']}")
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

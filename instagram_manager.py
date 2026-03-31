import os
import time
import random
import json
from instagrapi import Client
from dotenv import load_dotenv
from agent_logic import sales_agent

load_dotenv()

class InstagramManager:
    def __init__(self):
        self.cl = Client()
        self.session_file = "ig_session.json"
        self.username = os.getenv("IG_USERNAME")
        self.password = os.getenv("IG_PASSWORD")

    def login(self):
        """Login seguro con persistencia de sesión para evitar bloqueos."""
        try:
            if os.path.exists(self.session_file):
                print("[IG] Cargando sesión persistente...")
                self.cl.load_settings(self.session_file)
            
            # Intentar login (instagrapi usa la sesión cargada si existe)
            print(f"[IG] Intentando conectar como {self.username}...")
            self.cl.login(self.username, self.password)
            
            # Guardamos la sesión después del éxito
            self.cl.dump_settings(self.session_file)
            print(f"[IG] Conectado exitosamente.")
            
        except Exception as e:
            print(f"[IG] Error crítico en login: {e}")
            if "JSONDecodeError" in str(e):
                print("[IG] Instagram bloqueó la petición (Challenge). Reintentando en unos minutos...")
            raise e

    def monitor_dms(self):
        """Escucha mensajes directos y responde con el Cerebro GPT."""
        print("[IG] Iniciando monitoreo de DMs...")
        while True:
            try:
                # Obtenemos los hilos no leídos
                threads = self.cl.direct_threads(amount=10, selected_filter="unread")
                
                for thread in threads:
                    messages = thread.messages
                    if not messages:
                        continue
                    
                    last_msg = messages[0]
                    # Solo responder si el mensaje es de texto y NO es nuestro
                    if last_msg.item_type == 'text' and last_msg.user_id != self.cl.user_id:
                        print(f"[IG] Nuevo mensaje de {thread.thread_title}: {last_msg.text}")
                        
                        # Lógica de 'engaño' (Human-like behavior)
                        # 1. Simular tiempo de lectura
                        time.sleep(random.uniform(5, 12))
                        
                        # 2. Obtener respuesta del Agente
                        response_data = sales_agent.process_message(last_msg.text, context="instagram")
                        response_text = response_data["text"]
                        
                        # 3. Simular tiempo de escritura
                        writing_time = len(response_text) / 10 # aprox 10 caracteres por segundo
                        time.sleep(min(writing_time, 10)) 
                        
                        # 4. Enviar mensaje
                        self.cl.direct_answer(thread.id, response_text)
                        print(f"[IG] Respondido con éxito.")
                
                # Espera aleatoria larga entre chequeos para no parecer bot
                time.sleep(random.uniform(30, 90))
                
            except Exception as e:
                print(f"[IG] Error en monitoreo: {e}")
                time.sleep(300) # Esperar 5 min si hay error

def run_instagram_bot():
    ig = InstagramManager()
    if ig.username and ig.password:
        ig.login()
        ig.monitor_dms()
    else:
        print("[IG] Faltan credenciales de Instagram en .env")

if __name__ == "__main__":
    run_instagram_bot()

import os
import json
import base64
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

def generate_session():
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("❌ Error: Falta IG_USERNAME o IG_PASSWORD en el archivo .env")
        return

    cl = Client()
    print(f"[*] Intentando iniciar sesion local como {username}...")
    
    try:
        cl.login(username, password)
        print("[OK] Login exitoso en tu PC!")
        
        # Extraer la sesión como JSON y luego a Base64
        session_data = cl.get_settings()
        session_json = json.dumps(session_data)
        session_b64 = base64.b64encode(session_json.encode()).decode()
        
        print("\n" + "="*60)
        print("LLAVE DE SESION (Copia esto):")
        print("="*60 + "\n")
        print(session_b64)
        print("\n" + "="*60)
        print("INSTRUCCIONES:")
        print("1. Copia todo el codigo de arriba.")
        print("2. Anda a Railway -> Tu servicio 'web' -> Pestaña 'Variables'.")
        print("3. Crea una Variable nueva llamada: INSTAGRAM_SESSION_B64")
        print("4. Pega el codigo ahi y guardalo.")
        print("5. Reinicia el servicio y el bot deberia entrar sin problemas.")
        print("="*60)

    except Exception as e:
        print(f"❌ Error al generar la sesión: {e}")

if __name__ == "__main__":
    generate_session()

import os
import sys
from agent_logic import sales_agent
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def chat():
    print("\n" + "="*50)
    print("      🤖 ASISTENTE DE VENTAS AI - CONSOLA 🤖")
    print("="*50)
    print("Escribí tu consulta (o 'salir' para cerrar)\n")
    
    while True:
        try:
            user_input = input("👤 Vos: ")
            
            if user_input.lower() in ["salir", "exit", "quit", "chau"]:
                print("\n👋 ¡Hasta luego!")
                break
            
            if not user_input.strip():
                continue

            print("⏳ El asistente está buscando información...")
            
            # Procesar mensaje
            response = sales_agent.process_message(user_input, context="tienda")
            
            print(f"\n🤖 Asistente: {response['text']}")
            
            # Mostrar productos si se encontraron
            if response.get("products"):
                print("\n🛍️ Resultados de la tienda:")
                for i, p in enumerate(response["products"], 1):
                    # Limpiamos el precio si viene con HTML o raros
                    price = p.get('price', 'Consultar')
                    print(f"   {i}. {p['name']} - ${price}")
                    print(f"      Link: {p['permalink']}")
            
            print("\n" + "-"*30)

        except KeyboardInterrupt:
            print("\n\n👋 Sesión terminada.")
            break
        except Exception as e:
            print(f"\n❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    # Verificar API KEY antes de empezar
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: No se encontró la OPENAI_API_KEY en el archivo .env")
    else:
        chat()

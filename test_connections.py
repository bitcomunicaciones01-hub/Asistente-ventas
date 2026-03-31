import os
from dotenv import load_dotenv
from openai import OpenAI
from woocommerce import API

load_dotenv()

def test_openai():
    print("--- Probando OpenAI ---")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "tu_openai" in api_key:
            print("ERROR: Clave de OpenAI no configurada correctamente.")
            return
            
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Dime 'Conexión Exitosa'"}]
        )
        print(f"Respuesta: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error OpenAI: {e}")

def test_woo():
    print("\n--- Probando WooCommerce ---")
    try:
        url = os.getenv("WOO_URL")
        ck = os.getenv("WOO_CK")
        cs = os.getenv("WOO_CS")

        if not url or "tu-tienda" in url:
            print("ERROR: URL de WooCommerce no configurada correctamente.")
            return

        wcapi = API(
            url=url,
            consumer_key=ck,
            consumer_secret=cs,
            version="wc/v3"
        )
        res = wcapi.get("products", params={"per_page": 1})
        if res.status_code == 200:
            products = res.json()
            if products:
                print(f"Conexión exitosa. Encontrado producto: {products[0]['name']}")
            else:
                print("Conexión exitosa, pero no se encontraron productos.")
        else:
            print(f"Error Woo: Código {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Error WooCommerce: {e}")

if __name__ == "__main__":
    test_openai()
    test_woo()

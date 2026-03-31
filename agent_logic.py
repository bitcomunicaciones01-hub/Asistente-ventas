import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from woo_manager import woo_manager

load_dotenv()

class SalesAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini" # Modelo económico y potente

    def _get_system_prompt(self, context="tienda"):
        if context == "instagram":
            return (
                "Eres un asistente de ventas experto en Instagram para 'BIT Comunicaciones'. "
                "Tu objetivo es ser amable y persuasivo para cerrar ventas de repuestos. "
                "REGLAS OBLIGATORIAS DE FORMATO:\n"
                "1. Lista un MÁXIMO de 3 productos.\n"
                "2. ESTÁ ESTRICTAMENTE PROHIBIDO usar Markdown para links y la palabra 'http' o 'https'.\n"
                "3. Debes cambiar SIEMPRE 'https://' por 'www.' en las URLs de WooCommerce.\n"
                "4. Formato EXACTO por producto:\n\n"
                "   💻 [Nombre corto del producto]\n"
                "   💰 $[Precio]\n"
                "   👉 www.bitcomunicaciones.com/[ruta-del-producto]\n\n"
                "5. Deja una línea vacía antes y después de la URL para que el celular lo detecte correctamente.\n"
                "6. Si no encuentras el producto, ofrece WhatsApp con www.wa.me/543425482454"
            )
        else:
            return (
                "Eres un asistente de ventas de una tienda WooCommerce. "
                "Tu única misión es guiar al usuario de forma amable y profesional. "
                "REGLA DE ORO DE VISUALIZACIÓN: Está TERMINANTEMENTE PROHIBIDO usar listas numeradas (1., 2., 3...) o viñetas. "
                "Si la herramienta te devuelve productos, tu respuesta DEBE SER únicamente una frase corta como: '¡Mirá estas opciones que encontré para vos!'. "
                "NUNCA describas los productos en el texto, el sistema ya los muestra en la grilla horizontal de 3."
                "Sé servicial y persuasivo. Usa emojis."
                "SI NO HAY RESULTADOS: Sugiérele hablar con un humano por WhatsApp: https://wa.me/543425482454"
            )

    def process_message(self, user_message, context="tienda"):
        # Definimos las herramientas de búsqueda de productos
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Busca productos en la tienda por nombre o categoría",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "El nombre del producto a buscar"},
                            "category": {"type": "string", "description": "La categoría del producto"}
                        }
                    }
                }
            }
        ]

        messages = [
            {"role": "system", "content": self._get_system_prompt(context)},
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        
        # Manejar llamadas a herramientas (búsqueda de productos)
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                if function_name == "search_products":
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query")
                    print(f"[AGENT] Buscando productos con query: '{query}'")
                    
                    products = woo_manager.search_products(
                        query=query,
                        category=args.get("category")
                    )

                    # Si no encuentra nada, intentamos una búsqueda más simple (modelo)
                    if not products and len(query.split()) > 2:
                        simple_query = " ".join(query.split()[-2:]) # Tomamos las últimas palabras (modelo)
                        print(f"[AGENT] Reintentando con query simplificada: '{simple_query}'")
                        products = woo_manager.search_products(query=simple_query)
                    
                    # Añadimos el resultado de la herramienta al hilo
                    messages.append(response_message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "search_products",
                        "content": json.dumps(products)
                    })
            
            # Segunda llamada con los datos de productos
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return {
                "text": second_response.choices[0].message.content,
                "products": products if 'products' in locals() else []
            }

        return {
            "text": response_message.content,
            "products": []
        }

# Instancia global
sales_agent = SalesAgent()

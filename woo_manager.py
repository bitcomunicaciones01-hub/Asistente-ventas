import os
from woocommerce import API
from dotenv import load_dotenv

load_dotenv()

class WooManager:
    def __init__(self):
        self.wcapi = API(
            url=os.getenv("WOO_URL"),
            consumer_key=os.getenv("WOO_CK"),
            consumer_secret=os.getenv("WOO_CS"),
            version="wc/v3"
        )

    def search_products(self, query=None, category=None):
        """Busca productos por nombre o categoría."""
        params = {"status": "publish"}
        if query:
            params["search"] = query
        if category:
            params["category"] = category
        
        response = self.wcapi.get("products", params=params)
        if response.status_code == 200:
            products = response.json()
            return [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "price": p["price"],
                    "regular_price": p["regular_price"],
                    "sale_price": p["sale_price"],
                    "on_sale": p["on_sale"],
                    "permalink": p["permalink"],
                    "images": [img["src"] for img in p["images"]][:1],
                    "description": p["short_description"] or p["description"]
                }
                for p in products
            ]
        return []

    def get_product_details(self, product_id):
        """Obtiene detalles de un producto específico."""
        response = self.wcapi.get(f"products/{product_id}")
        if response.status_code == 200:
            return response.json()
        return None

# Instancia global para ser usada en el agente
woo_manager = WooManager()

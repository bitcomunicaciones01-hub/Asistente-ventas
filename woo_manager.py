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
        self.category_cache = {}

    def get_category_id(self, category_name):
        if not category_name:
            return None
        
        name_lower = category_name.lower().strip()
        
        # Si ya está en caché, usarla
        if name_lower in self.category_cache:
            return self.category_cache[name_lower]
            
        # Buscar en cache por coincidencias parciales si ya tiene elementos
        if self.category_cache:
            for cached_name, cat_id in self.category_cache.items():
                if name_lower in cached_name or cached_name in name_lower:
                    return cat_id

        # Poblar cargando categorías de WooCommerce (Página 1)
        try:
            response = self.wcapi.get("products/categories", params={"per_page": 100})
            if response.status_code == 200:
                for cat in response.json():
                    self.category_cache[cat["name"].lower().strip()] = cat["id"]
                    self.category_cache[cat["slug"].lower().strip()] = cat["id"]
        except Exception as e:
            print(f"[WOO_MANAGER] Error cargando categorías de pág 1: {e}")
            
        # Si no se encuentra, poblar Página 2
        if name_lower not in self.category_cache:
            try:
                response = self.wcapi.get("products/categories", params={"per_page": 100, "page": 2})
                if response.status_code == 200:
                    for cat in response.json():
                        self.category_cache[cat["name"].lower().strip()] = cat["id"]
                        self.category_cache[cat["slug"].lower().strip()] = cat["id"]
            except Exception as e:
                print(f"[WOO_MANAGER] Error cargando categorías de pág 2: {e}")

        # Coincidencia exacta
        if name_lower in self.category_cache:
            return self.category_cache[name_lower]
            
        # Coincidencia parcial
        for cached_name, cat_id in self.category_cache.items():
            if name_lower in cached_name or cached_name in name_lower:
                return cat_id
                
        return None

    def clean_query(self, query):
        if not query:
            return ""
        q = query.lower()
        # Eliminar conectores y artículos comunes
        stop_words = ["para", "de", "con", "del", "en", "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "a", "al"]
        words = q.split()
        cleaned_words = [w for w in words if w not in stop_words]
        return " ".join(cleaned_words)

    def _format_products(self, response):
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

    def search_products(self, query=None, category=None):
        """Busca productos por nombre o categoría con fallbacks inteligentes."""
        category_id = None
        if category:
            if str(category).isdigit():
                category_id = int(category)
            else:
                category_id = self.get_category_id(category)
                print(f"[WOO_MANAGER] Traduciendo categoría '{category}' -> ID: {category_id}")
        
        params = {
            "status": "publish",
            "stock_status": "instock"
        }
        if category_id:
            params["category"] = str(category_id)

        # Caso sin término de búsqueda (solo por categoría)
        if not query:
            response = self.wcapi.get("products", params=params)
            return self._format_products(response)

        cleaned_query = self.clean_query(query)
        print(f"[WOO_MANAGER] Búsqueda original: '{query}' -> Limpia: '{cleaned_query}'")

        # 1. Búsqueda principal limpia
        params["search"] = cleaned_query
        response = self.wcapi.get("products", params=params)
        products = self._format_products(response)

        # 2. Fallback: Remover palabras genéricas restrictivas
        if not products:
            generic_words = ["notebook", "netbook", "laptop", "pc", "computadora", "repuesto", "repuestos", "original", "originales", "funcionando", "funcionan"]
            words = cleaned_query.split()
            filtered_words = [w for w in words if w not in generic_words]
            if filtered_words and len(filtered_words) < len(words):
                fallback_query = " ".join(filtered_words)
                print(f"[WOO_MANAGER] Fallback 1: Reintentando sin palabras genéricas: '{fallback_query}'")
                params["search"] = fallback_query
                response = self.wcapi.get("products", params=params)
                products = self._format_products(response)

        # 3. Fallback: Buscar usando solo las primeras 2 palabras clave
        if not products and len(cleaned_query.split()) > 1:
            first_words = " ".join(cleaned_query.split()[:2])
            print(f"[WOO_MANAGER] Fallback 2: Reintentando con primeras palabras: '{first_words}'")
            params["search"] = first_words
            response = self.wcapi.get("products", params=params)
            products = self._format_products(response)

        # 4. Fallback: Si no hay resultados con categoría, buscar globalmente sin categoría
        if not products and category_id:
            print(f"[WOO_MANAGER] Fallback 3: Reintentando sin restricción de categoría")
            params_no_cat = {
                "status": "publish",
                "stock_status": "instock",
                "search": cleaned_query
            }
            response = self.wcapi.get("products", params=params_no_cat)
            products = self._format_products(response)

        # 5. Fallback: Si busca en Equipos Funcionando y no encontró nada específico, devolver todos los equipos en stock
        equipos_id = self.get_category_id("Equipos Funcionando")
        if not products and category_id == equipos_id and equipos_id:
            print("[WOO_MANAGER] Fallback 4: Retornando stock general de Equipos Funcionando")
            params_all_equipos = {
                "status": "publish",
                "stock_status": "instock",
                "category": str(equipos_id)
            }
            response = self.wcapi.get("products", params=params_all_equipos)
            products = self._format_products(response)

        return products

    def get_product_details(self, product_id):
        """Obtiene detalles de un producto específico."""
        response = self.wcapi.get(f"products/{product_id}")
        if response.status_code == 200:
            return response.json()
        return None

# Instancia global para ser usada en el agente
woo_manager = WooManager()

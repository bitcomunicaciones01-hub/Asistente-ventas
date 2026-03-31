import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from agent_logic import sales_agent
from instagram_manager import run_instagram_bot
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sales AI Assistant API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del widget
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = "tienda" # "tienda" o "instagram"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Sales AI Agent running"}

@app.post("/chat")
async def chat_with_agent(chat: ChatMessage):
    """Procesa mensajes del chat widget o Instagram."""
    try:
        response = sales_agent.process_message(chat.message, chat.context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Inicia el monitoreo de Instagram en segundo plano al arrancar el servidor."""
    from threading import Thread
    print("[INFO] Iniciando monitoreo de Instagram en segundo plano (Modo Robusto)...")
    thread = Thread(target=run_instagram_bot)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

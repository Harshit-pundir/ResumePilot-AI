from fastapi import FastAPI
from routes.history2 import router as history_router
from routes.ai2 import router as ai_router
from routes.home2 import router as home_router
from fastapi.staticfiles import StaticFiles

def create_app():
    app = FastAPI(title="ResumePilot AI")

    @app.get("/api/health")
    def health():
        return {"status":"ok"}

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(history_router)
    app.include_router(ai_router)
    app.include_router(home_router)
    
    return app

app = create_app()





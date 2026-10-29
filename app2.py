from fastapi import FastAPI
from routes.history2 import router as history_router

def create_app():
    app = FastAPI(title="ResumePilot AI")

    @app.get("/api/health")
    def health():
        return {"status":"ok"}

    app.include_router(history_router)
    
    return app

app = create_app()





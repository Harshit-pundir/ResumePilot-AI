from fastapi import FastAPI

def create_app():
    app = FastAPI(title="ResumePilot AI")

    @app.get("/api/health")
    def health():
        return {"status":"ok"}
    
    return app

app = create_app()





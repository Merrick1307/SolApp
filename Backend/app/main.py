from fastapi import FastAPI

from .api import api_router

app = FastAPI(title="Solana Blockchain Integration Service")

app.include_router(api_router)


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
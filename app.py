
from fastapi import FastAPI
from routers import ai, configs , siteparse    # Import your routers

app = FastAPI()

# Include routers
app.include_router(ai.router)
app.include_router(configs.router)
app.include_router(siteparse.router)
# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Hashtag Generator API!"}
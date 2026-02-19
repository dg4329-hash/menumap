"""
MenuMap - Web API
FastAPI backend for the MenuMap web app
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
from matcher import MenuMatcher
from ai_coach import get_recommendation

app = FastAPI(title="MenuMap", description="AI-powered campus dining assistant")

# Initialize matcher
matcher = MenuMatcher()


class SearchRequest(BaseModel):
    query: str
    limit: int = 8


class MenuItem(BaseModel):
    name: str
    location: str
    period: str
    category: str
    calories: int | None
    protein: float | None
    carbs: float | None
    fat: float | None
    dietary_tags: list[str]
    score: float
    match_reasons: list[str]


class SearchResponse(BaseModel):
    query: str
    results: list[MenuItem]
    total_found: int


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main app"""
    html_path = Path(__file__).parent / "static" / "index.html"
    return FileResponse(html_path)


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search for menu items matching the query"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = matcher.search(request.query, limit=request.limit)

    return SearchResponse(
        query=request.query,
        results=[
            MenuItem(
                name=r.name,
                location=r.location,
                period=r.period,
                category=r.category,
                calories=r.calories,
                protein=r.protein,
                carbs=r.carbs,
                fat=r.fat,
                dietary_tags=r.dietary_tags,
                score=r.score,
                match_reasons=r.match_reasons
            )
            for r in results
        ],
        total_found=len(results)
    )


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    response: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Get AI-powered meal recommendation"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = get_recommendation(request.message)
        return ChatResponse(
            message=request.message,
            response=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats():
    """Get menu statistics"""
    return matcher.get_stats()


@app.get("/api/locations")
async def locations():
    """Get all dining locations"""
    return {"locations": matcher.get_locations()}


# Serve static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import asyncio
from quiz_solver import QuizSolver

# Load environment variables
load_dotenv()

app = FastAPI(title="LLM Quiz Solver")

# Get credentials from environment
YOUR_EMAIL = os.getenv("EMAIL")
YOUR_SECRET = os.getenv("SECRET")

if not YOUR_EMAIL or not YOUR_SECRET:
    raise ValueError("Please set YOUR_EMAIL and YOUR_SECRET in .env file")

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

@app.get("/")
async def root():
    return {"status": "Quiz Solver is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/quiz")
async def handle_quiz(request: QuizRequest):
    """Main endpoint that receives quiz tasks"""
    
    # Check if secret matches
    if request.secret != YOUR_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    if request.email != YOUR_EMAIL:
        raise HTTPException(status_code=400, detail="Invalid email")
    
    print(f"✅ Received quiz request for: {request.url}")
    
    # Start solving in background
    solver = QuizSolver(request.email, request.secret)
    asyncio.create_task(solver.solve_quiz_chain(request.url))
    
    return {
        "status": "accepted",
        "message": f"Started solving quiz at {request.url}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
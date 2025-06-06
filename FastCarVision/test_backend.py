#!/usr/bin/env python3
"""
Simple test backend to verify FastAPI setup
"""

from fastapi import FastAPI
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="FastCarVision Test", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FastCarVision Test Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Test backend is working"}

if __name__ == "__main__":
    print("🚗 Starting Test Backend on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
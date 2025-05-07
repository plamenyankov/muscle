from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import API routers
from app.api.users import router as users_router
from app.api.exercises import router as exercises_router
from app.api.workouts import router as workouts_router
from app.api.workout_logs import router as workout_logs_router
from app.api.progress import router as progress_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Muscle - Fitness Tracking App",
    description="Track your fitness training sessions and monitor progress over time.",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Root endpoint
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Muscle - Fitness Tracker"}
    )

# Login page
@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "Login - Muscle Fitness Tracker"}
    )

# Register page
@app.get("/register")
async def register(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Register - Muscle Fitness Tracker"}
    )

# Dashboard page
@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard - Muscle Fitness Tracker"}
    )

# Exercises page
@app.get("/exercises")
async def exercises(request: Request):
    return templates.TemplateResponse(
        "exercises.html",
        {"request": request, "title": "Exercises - Muscle Fitness Tracker"}
    )

# Create Plan page
@app.get("/create-plan")
async def create_plan_page(request: Request):
    return templates.TemplateResponse(
        "create-plan.html",
        {"request": request, "title": "Create Training Plan - Muscle Fitness Tracker"}
    )

# Workouts page - displays all workout templates
@app.get("/workouts")
async def workouts_page(request: Request):
    return templates.TemplateResponse(
        "workouts.html",
        {"request": request, "title": "My Workouts - Muscle Fitness Tracker"}
    )

# Workout details page - displays a specific workout template
@app.get("/workout/{template_id}")
async def workout_details_page(request: Request, template_id: int):
    return templates.TemplateResponse(
        "workout-details.html",
        {"request": request, "title": "Workout Details - Muscle Fitness Tracker", "template_id": template_id}
    )

# Edit workout page - allows editing a specific workout template
@app.get("/edit-workout/{template_id}")
async def edit_workout_page(request: Request, template_id: int):
    return templates.TemplateResponse(
        "edit-workout.html",
        {"request": request, "title": "Edit Workout - Muscle Fitness Tracker", "template_id": template_id}
    )

# Start workout page - allows starting a workout session based on a template
@app.get("/start-workout/{template_id}")
async def start_workout_page(request: Request, template_id: int):
    return templates.TemplateResponse(
        "start-workout.html",
        {"request": request, "title": "Start Workout - Muscle Fitness Tracker", "template_id": template_id}
    )

# Training logs page - displays all workout logs/history
@app.get("/logs")
async def logs_page(request: Request):
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "title": "Training Logs - Muscle Fitness Tracker"}
    )

# Training log details page - shows a specific workout session
@app.get("/logs/{session_id}")
async def log_details_page(request: Request, session_id: int):
    return templates.TemplateResponse(
        "log-details.html",
        {"request": request, "title": "Workout Session - Muscle Fitness Tracker", "session_id": session_id}
    )

# Progress tracking page - shows workout progress metrics and charts
@app.get("/progress")
async def progress_page(request: Request):
    return templates.TemplateResponse(
        "progress.html",
        {"request": request, "title": "Progress Tracking - Muscle Fitness Tracker"}
    )

# API health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

# Include API routers
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(exercises_router, prefix="/api/exercises", tags=["exercises"])
app.include_router(workouts_router, prefix="/api/workouts", tags=["workouts"])
app.include_router(workout_logs_router, prefix="/api/logs", tags=["workout_logs"])
app.include_router(progress_router, prefix="/api/progress", tags=["progress"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

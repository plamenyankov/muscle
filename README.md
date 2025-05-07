# Muscle - Fitness Tracking Application

A FastAPI-based application for tracking your fitness training sessions. Plan workouts, log your training, and analyze your progress over time.

## Features

- User authentication and profile management
- Browse exercises by muscle group and equipment type
- Create custom workout templates
- Log workout sessions with sets, reps, and weights
- Track progress and view performance metrics
- Mobile-friendly UI for gym use

## Tech Stack

- **Backend**: Python 3.9 with FastAPI
- **Database**: MySQL (direct SQL queries, no ORM)
- **Frontend**: HTML, JavaScript with Tailwind CSS
- **Authentication**: JWT tokens

## Setup Instructions

### Prerequisites

- Python 3.9 or later
- MySQL 8.0 or later
- Docker and Docker Compose (optional)

### Environment Setup

1. Clone the repository
   ```
   git clone <repository-url>
   cd muscle
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Create `.env` file from example
   ```
   cp env.example .env
   ```
   Edit the `.env` file with your database credentials and other configuration.

### Database Setup

#### Option 1: Manual Setup

1. Create a MySQL database named `muscle_fitness`
2. Run the schema script to create tables
   ```
   mysql -u <username> -p muscle_fitness < db_schema.sql
   ```

#### Option 2: Using Docker

1. Start the application with Docker Compose
   ```
   docker-compose up -d
   ```
   This will create the MySQL database and initialize the schema automatically.

### Running the Application

#### Option 1: Local Development

1. Start the application
   ```
   uvicorn app.main:app --reload
   ```

2. Access the application at http://localhost:8000

#### Option 2: Using Docker

1. Start the application with Docker Compose
   ```
   docker-compose up -d
   ```

2. Access the application at http://localhost:8000

## API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### Creating a Workout Template

1. Sign in to your account
2. Navigate to "Workouts" section
3. Click "Create New Template"
4. Name your template (e.g., "Chest Day")
5. Add exercises, specifying sets, reps, and target weights
6. Save the template

### Logging a Workout

1. Sign in to your account
2. Select an existing template or create a new workout
3. For each exercise, record the actual sets, reps, and weights
4. Mark the workout as completed when done

### Viewing Progress

1. Navigate to the "Progress" section
2. View performance metrics for specific exercises
3. Track improvements over time

## Deployment

### Local or Custom Deployment

1. Ensure your production database is set up
2. Update `.env` file with production settings
3. Build the Docker image
   ```
   docker build -t muscle-app .
   ```
4. Deploy the container to your preferred hosting service

### Railway Deployment

For a streamlined deployment process, this application can be deployed to [Railway](https://railway.app):

1. Fork this repository to your GitHub account
2. Sign up for a Railway account and create a new project
3. Select "Deploy from GitHub repo" and choose your forked repository
4. Add a MySQL service to your project
5. Configure environment variables in the Railway dashboard
6. Deploy the application

For detailed step-by-step instructions, see [`deployment-guide.md`](deployment-guide.md) in this repository.

## License

[MIT License](LICENSE)

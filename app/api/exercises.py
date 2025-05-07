from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.db.connection import execute_query

router = APIRouter()

class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None
    muscle_group_id: int
    equipment_type: str
    is_compound: bool = False

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    exercise_id: int
    created_at: str
    muscle_group_name: Optional[str] = None

class MuscleGroup(BaseModel):
    muscle_group_id: int
    name: str
    description: Optional[str] = None

@router.get("/", response_model=List[Exercise])
async def get_exercises(
    user_id: Optional[int] = None,
    muscle_group: Optional[int] = None,
    equipment_type: Optional[str] = None,
    is_compound: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get exercises with optional filtering by muscle group, equipment type, etc.
    """
    # Get exercises with muscle group name
    query = """
    SELECT e.*, mg.name as muscle_group_name
    FROM exercises e
    LEFT JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
    WHERE 1=1
    """

    params = []

    if muscle_group is not None:
        query += " AND e.muscle_group_id = %s"
        params.append(muscle_group)

    if equipment_type is not None:
        query += " AND e.equipment_type = %s"
        params.append(equipment_type)

    if is_compound is not None:
        query += " AND e.is_compound = %s"
        params.append(is_compound)

    if search is not None:
        query += " AND (e.name LIKE %s OR e.description LIKE %s)"
        search_param = f"%{search}%"
        params.append(search_param)
        params.append(search_param)

    # Order by name for better UI display
    query += " ORDER BY e.name"

    # Limit the results
    query += " LIMIT %s"
    params.append(limit)

    try:
        exercises = execute_query(query, tuple(params))
        return exercises
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{exercise_id}", response_model=Exercise)
async def get_exercise(exercise_id: int):
    """
    Get a specific exercise by ID
    """
    query = "SELECT * FROM exercises WHERE exercise_id = %s"

    try:
        results = execute_query(query, (exercise_id,))
        if not results:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return results[0]
    except Exception as e:
        if "not found" in str(e):
            raise
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/", response_model=Exercise)
async def create_exercise(exercise: ExerciseCreate):
    """
    Create a new exercise
    """
    query = """
    INSERT INTO exercises (name, description, muscle_group_id, equipment_type, is_compound)
    VALUES (%s, %s, %s, %s, %s)
    """

    try:
        # Check if muscle group exists
        muscle_check = execute_query(
            "SELECT * FROM muscle_groups WHERE muscle_group_id = %s",
            (exercise.muscle_group_id,)
        )

        if not muscle_check:
            raise HTTPException(status_code=400, detail="Invalid muscle group ID")

        # Insert the exercise
        exercise_id = execute_query(
            query,
            (
                exercise.name,
                exercise.description,
                exercise.muscle_group_id,
                exercise.equipment_type,
                exercise.is_compound
            ),
            fetch=False
        )

        # Get the created exercise
        created = execute_query(
            "SELECT * FROM exercises WHERE exercise_id = %s",
            (exercise_id,)
        )

        return created[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/muscle-groups/", response_model=List[MuscleGroup])
async def get_muscle_groups():
    """
    Get all muscle groups
    """
    query = "SELECT * FROM muscle_groups ORDER BY name"

    try:
        muscle_groups = execute_query(query)
        return muscle_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/equipment-types/", response_model=List[str])
async def get_equipment_types():
    """
    Get all equipment types (from the ENUM)
    """
    try:
        # This uses information_schema to get the ENUM values
        query = """
        SELECT SUBSTRING(COLUMN_TYPE, 6, LENGTH(COLUMN_TYPE) - 6) as enum_values
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'muscle_fitness'
        AND TABLE_NAME = 'exercises'
        AND COLUMN_NAME = 'equipment_type'
        """

        result = execute_query(query)

        if not result:
            return []

        # Parse the ENUM string, format is like: 'machine','free_weight','bodyweight','other'
        enum_str = result[0]['enum_values']
        enum_values = [val.replace("'", "") for val in enum_str.split(",")]

        return enum_values
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

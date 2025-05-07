from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, validator, Field
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
from app.db.connection import execute_query, get_connection

router = APIRouter()

class ExerciseSetBase(BaseModel):
    exercise_id: int
    set_number: int
    reps: int
    weight: Optional[float] = None
    completed: bool = True
    perceived_difficulty: Optional[int] = None
    notes: Optional[str] = None

class ExerciseSetCreate(ExerciseSetBase):
    pass

class ExerciseSet(ExerciseSetBase):
    set_id: int
    session_id: int

# For request models - accept datetime or string
class WorkoutSessionBase(BaseModel):
    template_id: Optional[int] = None
    session_date: Union[datetime, str]  # Accept either datetime or string
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None

    # Validator to convert string to datetime
    @validator('session_date', pre=True)
    def parse_session_date(cls, value):
        if isinstance(value, str):
            try:
                # Try to parse ISO format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try to parse YYYY-MM-DD format
                    return datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    # If all parsing fails, use current date
                    return datetime.now()
        return value

class WorkoutSessionCreate(WorkoutSessionBase):
    exercise_sets: List[ExerciseSetCreate]

# For response models - always use string for datetime fields
class WorkoutSessionRead(BaseModel):
    session_id: int
    user_id: int
    template_id: Optional[int] = None
    session_date: str  # Always string in responses
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    template_name: Optional[str] = None
    set_count: Optional[int] = 0

class WorkoutSessionDetail(WorkoutSessionRead):
    exercise_sets: List[ExerciseSet]

@router.get("/", response_model=List[WorkoutSessionRead])
async def get_workout_sessions(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get workout sessions for a user with optional date filtering
    """
    query_parts = ["""
        SELECT ws.*, wt.name as template_name,
        (SELECT COUNT(*) FROM exercise_sets WHERE session_id = ws.session_id) as set_count
        FROM workout_sessions ws
        LEFT JOIN workout_templates wt ON ws.template_id = wt.template_id
        WHERE ws.user_id = %s
    """]
    params = [user_id]

    if start_date:
        query_parts.append("AND ws.session_date >= %s")
        params.append(start_date)

    if end_date:
        query_parts.append("AND ws.session_date <= %s")
        params.append(end_date)

    query_parts.append("ORDER BY ws.session_date DESC LIMIT %s OFFSET %s")
    params.append(limit)
    params.append(offset)

    query = " ".join(query_parts)

    try:
        sessions = execute_query(query, tuple(params))

        # Convert all datetime objects to ISO format strings
        for session in sessions:
            if isinstance(session.get('session_date'), datetime):
                session['session_date'] = session['session_date'].isoformat()
            if isinstance(session.get('created_at'), datetime):
                session['created_at'] = session['created_at'].isoformat()
            if isinstance(session.get('completed_at'), datetime):
                session['completed_at'] = session['completed_at'].isoformat()

            # Make sure duration is an integer
            if session.get('duration_minutes') is not None:
                session['duration_minutes'] = int(session['duration_minutes'])

        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{session_id}", response_model=WorkoutSessionDetail)
async def get_workout_session(session_id: int):
    """
    Get a specific workout session by ID, including its exercise sets
    """
    session_query = """
    SELECT ws.*, wt.name as template_name
    FROM workout_sessions ws
    LEFT JOIN workout_templates wt ON ws.template_id = wt.template_id
    WHERE ws.session_id = %s
    """

    sets_query = """
    SELECT es.*, e.name as exercise_name, e.equipment_type, mg.name as muscle_group_name
    FROM exercise_sets es
    JOIN exercises e ON es.exercise_id = e.exercise_id
    LEFT JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
    WHERE es.session_id = %s
    ORDER BY es.exercise_id, es.set_number
    """

    try:
        # Get session
        session_results = execute_query(session_query, (session_id,))
        if not session_results:
            raise HTTPException(status_code=404, detail="Workout session not found")

        session = session_results[0]

        # Ensure session_date is a string (in case the execute_query didn't convert it)
        if isinstance(session.get('session_date'), datetime):
            session['session_date'] = session['session_date'].isoformat()

        # Get exercise sets
        sets = execute_query(sets_query, (session_id,))

        # Combine the results
        session['exercise_sets'] = sets

        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/", response_model=WorkoutSessionDetail)
async def create_workout_session(session: WorkoutSessionCreate, user_id: int):
    """
    Create a new workout session with exercise sets
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Convert session date to proper format if it's a string
            session_date = session.session_date
            if isinstance(session_date, str):
                try:
                    # Try to parse in case it's a string
                    session_date = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                except:
                    # If that fails, use current date
                    session_date = datetime.now()

            # Ensure duration_minutes is a positive integer (minimum 1 minute)
            duration_minutes = 1
            if session.duration_minutes is not None:
                try:
                    duration_minutes = max(1, int(session.duration_minutes))
                except (ValueError, TypeError):
                    # If conversion fails, default to 1 minute
                    duration_minutes = 1

            print(f"Debug - Duration minutes: {duration_minutes}, raw value: {session.duration_minutes}")

            # Insert session
            session_query = """
            INSERT INTO workout_sessions
            (user_id, template_id, session_date, duration_minutes, notes)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                session_query,
                (
                    user_id,
                    session.template_id,
                    session_date,
                    duration_minutes,
                    session.notes
                )
            )
            session_id = cursor.lastrowid

            # Insert exercise sets
            if session.exercise_sets:
                sets_query = """
                INSERT INTO exercise_sets
                (session_id, exercise_id, set_number, reps, weight, completed, perceived_difficulty, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                for exercise_set in session.exercise_sets:
                    cursor.execute(
                        sets_query,
                        (
                            session_id,
                            exercise_set.exercise_id,
                            exercise_set.set_number,
                            exercise_set.reps,
                            exercise_set.weight,
                            exercise_set.completed,
                            exercise_set.perceived_difficulty,
                            exercise_set.notes
                        )
                    )

            connection.commit()

            # Get the created session with sets
            result = await get_workout_session(session_id)

            # Ensure session_date is a string in the response
            if isinstance(result.get('session_date'), datetime):
                result['session_date'] = result['session_date'].isoformat()

            return result

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

@router.put("/{session_id}", response_model=WorkoutSessionDetail)
async def update_workout_session(session_id: int, session: WorkoutSessionCreate, user_id: int):
    """
    Update a workout session and its exercise sets
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Check if session exists and belongs to user
            check_query = "SELECT * FROM workout_sessions WHERE session_id = %s AND user_id = %s"
            cursor.execute(check_query, (session_id, user_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Workout session not found or not owned by user")

            # Convert session date
            session_date = session.session_date
            if isinstance(session_date, str):
                try:
                    # Try to parse in case it's a string
                    session_date = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                except:
                    # If that fails, use current date
                    session_date = datetime.now()

            # Update session
            session_query = """
            UPDATE workout_sessions
            SET template_id = %s, session_date = %s, duration_minutes = %s, notes = %s
            WHERE session_id = %s
            """
            cursor.execute(
                session_query,
                (
                    session.template_id,
                    session_date,
                    session.duration_minutes,
                    session.notes,
                    session_id
                )
            )

            # Delete existing exercise sets
            cursor.execute("DELETE FROM exercise_sets WHERE session_id = %s", (session_id,))

            # Insert new exercise sets
            if session.exercise_sets:
                sets_query = """
                INSERT INTO exercise_sets
                (session_id, exercise_id, set_number, reps, weight, completed, perceived_difficulty, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                for exercise_set in session.exercise_sets:
                    cursor.execute(
                        sets_query,
                        (
                            session_id,
                            exercise_set.exercise_id,
                            exercise_set.set_number,
                            exercise_set.reps,
                            exercise_set.weight,
                            exercise_set.completed,
                            exercise_set.perceived_difficulty,
                            exercise_set.notes
                        )
                    )

            connection.commit()

            # Get the updated session with sets
            result = await get_workout_session(session_id)

            # Ensure session_date is a string in the response
            if isinstance(result.get('session_date'), datetime):
                result['session_date'] = result['session_date'].isoformat()

            return result

    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

@router.delete("/{session_id}")
async def delete_workout_session(session_id: int, user_id: int):
    """
    Delete a workout session
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Check if session exists and belongs to user
            check_query = "SELECT * FROM workout_sessions WHERE session_id = %s AND user_id = %s"
            cursor.execute(check_query, (session_id, user_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Workout session not found or not owned by user")

            # Delete session (cascade will delete sets)
            delete_query = "DELETE FROM workout_sessions WHERE session_id = %s"
            cursor.execute(delete_query, (session_id,))

            connection.commit()

            return {"message": "Workout session deleted successfully"}

    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

@router.put("/{session_id}/complete")
async def complete_workout_session(session_id: int, user_id: int):
    """
    Mark a workout session as completed
    """
    try:
        # Check if session exists and belongs to user
        check_query = "SELECT * FROM workout_sessions WHERE session_id = %s AND user_id = %s"
        check_results = execute_query(check_query, (session_id, user_id))

        if not check_results:
            raise HTTPException(status_code=404, detail="Workout session not found or not owned by user")

        # Update completed_at timestamp
        update_query = "UPDATE workout_sessions SET completed_at = CURRENT_TIMESTAMP WHERE session_id = %s"
        execute_query(update_query, (session_id,), fetch=False)

        return {"message": "Workout session marked as completed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats/exercise/{exercise_id}", response_model=List[dict])
async def get_exercise_stats(exercise_id: int, user_id: int, limit: int = 10):
    """
    Get statistics for a specific exercise
    """
    query = """
    SELECT
        es.session_id,
        ws.session_date,
        MAX(es.weight) as max_weight,
        SUM(es.reps) as total_reps,
        COUNT(es.set_id) as total_sets,
        AVG(es.perceived_difficulty) as avg_difficulty
    FROM exercise_sets es
    JOIN workout_sessions ws ON es.session_id = ws.session_id
    WHERE es.exercise_id = %s AND ws.user_id = %s AND es.completed = TRUE
    GROUP BY es.session_id, ws.session_date
    ORDER BY ws.session_date DESC
    LIMIT %s
    """

    try:
        stats = execute_query(query, (exercise_id, user_id, limit))
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

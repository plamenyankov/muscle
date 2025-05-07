from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.connection import execute_query

router = APIRouter()

@router.get("/overview")
async def get_progress_overview(user_id: int, time_range: str = "all"):
    """
    Get summary statistics for the progress dashboard overview
    """
    try:
        # Get overall workout count
        count_query = """
        SELECT COUNT(*) as workout_count
        FROM workout_sessions
        WHERE user_id = %s
        """
        params = [user_id]

        if time_range != "all":
            # Convert time_range to a SQL interval
            interval = get_time_interval(time_range)
            count_query += " AND session_date >= DATE_SUB(NOW(), INTERVAL " + interval + ")"

        workout_count = execute_query(count_query, tuple(params))

        # Get total volume lifted
        volume_query = """
        SELECT IFNULL(SUM(es.weight * es.reps), 0) as total_volume
        FROM exercise_sets es
        JOIN workout_sessions ws ON es.session_id = ws.session_id
        WHERE ws.user_id = %s
        """
        params = [user_id]

        if time_range != "all":
            volume_query += " AND ws.session_date >= DATE_SUB(NOW(), INTERVAL " + interval + ")"

        volume_result = execute_query(volume_query, tuple(params))

        # Get total workout duration
        duration_query = """
        SELECT IFNULL(SUM(duration_minutes), 0) as total_duration
        FROM workout_sessions
        WHERE user_id = %s
        """
        params = [user_id]

        if time_range != "all":
            duration_query += " AND session_date >= DATE_SUB(NOW(), INTERVAL " + interval + ")"

        duration_result = execute_query(duration_query, tuple(params))

        return {
            "workout_count": workout_count[0].get("workout_count", 0) if workout_count else 0,
            "total_volume": volume_result[0].get("total_volume", 0) if volume_result else 0,
            "total_duration": duration_result[0].get("total_duration", 0) if duration_result else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/consistency")
async def get_workout_consistency(user_id: int, time_range: str = "year"):
    """
    Get workout frequency data for heatmap/calendar visualization
    """
    try:
        # Get interval based on time_range
        interval = get_time_interval(time_range)

        # Use a simpler query that's compatible with MySQL 8.0
        query = """
        SELECT
            DATE(session_date) as workout_date,
            COUNT(*) as workout_count,
            IFNULL(SUM(duration_minutes), 0) as total_minutes
        FROM workout_sessions
        WHERE user_id = %s
          AND session_date >= DATE_SUB(NOW(), INTERVAL """ + interval + """)
        GROUP BY workout_date
        ORDER BY workout_date
        """

        result = execute_query(query, (user_id,))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/exercise/{exercise_id}")
async def get_exercise_progress(
    exercise_id: int,
    user_id: int,
    metric: str = "weight",
    time_range: str = "all",
    aggregation: str = "session"
):
    """
    Get progress data for a specific exercise
    """
    try:
        # Select the appropriate value column based on metric
        if metric == "weight":
            # Get max weight for each workout
            value_col = "MAX(es.weight)"
        elif metric == "volume":
            # Calculate volume (weight × reps)
            value_col = "SUM(es.weight * es.reps)"
        elif metric == "reps":
            # Get max reps
            value_col = "MAX(es.reps)"
        elif metric == "estimated-1rm":
            # Estimate 1RM using Brzycki formula: weight × (36 / (37 - reps))
            value_col = "MAX(es.weight * (36 / (37 - LEAST(es.reps, 36))))"
        else:
            value_col = "MAX(es.weight)"

        # Time grouping
        if aggregation == "weekly":
            date_col = "DATE(DATE_SUB(ws.session_date, INTERVAL WEEKDAY(ws.session_date) DAY))"
        elif aggregation == "monthly":
            date_col = "DATE_FORMAT(ws.session_date, '%Y-%m-01')"
        else:  # Default to session-level
            date_col = "DATE(ws.session_date)"

        query = f"""
        SELECT
            {date_col} as date,
            {value_col} as value,
            MAX(ws.session_id) as session_id
        FROM exercise_sets es
        JOIN workout_sessions ws ON es.session_id = ws.session_id
        WHERE es.exercise_id = %s AND ws.user_id = %s AND es.completed = TRUE
        """

        params = [exercise_id, user_id]

        # Add time range filter if not "all"
        if time_range != "all":
            interval = get_time_interval(time_range)
            query += " AND ws.session_date >= DATE_SUB(NOW(), INTERVAL " + interval + ")"

        query += f" GROUP BY date ORDER BY date"

        result = execute_query(query, tuple(params))

        # Get exercise details
        exercise_query = """
        SELECT name, description
        FROM exercises
        WHERE exercise_id = %s
        """
        exercise_details = execute_query(exercise_query, (exercise_id,))

        return {
            "exercise": exercise_details[0] if exercise_details else {},
            "progress": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/volume-by-muscle")
async def get_volume_by_muscle_group(user_id: int, time_range: str = "month"):
    """
    Get total volume lifted by muscle group for radar chart
    """
    try:
        interval = get_time_interval(time_range)

        # Use a simpler query that's compatible with MySQL 8.0
        query = """
        SELECT
            mg.name as muscle_group,
            IFNULL(SUM(es.weight * es.reps), 0) as total_volume,
            COUNT(DISTINCT ws.session_id) as session_count
        FROM exercise_sets es
        JOIN workout_sessions ws ON es.session_id = ws.session_id
        JOIN exercises e ON es.exercise_id = e.exercise_id
        JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
        WHERE ws.user_id = %s
          AND ws.session_date >= DATE_SUB(NOW(), INTERVAL """ + interval + """)
        GROUP BY muscle_group
        ORDER BY total_volume DESC
        """

        result = execute_query(query, (user_id,))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/personal-records")
async def get_personal_records(user_id: int):
    """
    Get personal records for all exercises
    """
    try:
        # Further simplified query for MySQL compatibility
        query = """
        SELECT
            e.exercise_id,
            e.name as exercise_name,
            MAX(es.weight) as max_weight,
            mg.name as muscle_group,
            MAX(ws.session_date) as date_achieved
        FROM exercise_sets es
        JOIN workout_sessions ws ON es.session_id = ws.session_id
        JOIN exercises e ON es.exercise_id = e.exercise_id
        JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
        WHERE ws.user_id = %s AND es.completed = TRUE
        GROUP BY e.exercise_id, e.name, muscle_group
        ORDER BY max_weight DESC
        LIMIT 10
        """

        result = execute_query(query, (user_id,))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/history")
async def get_workout_history(user_id: int, limit: int = 20):
    """
    Get recent workout sessions for comparisons
    """
    try:
        query = """
        SELECT
            ws.session_id,
            ws.session_date,
            ws.duration_minutes,
            wt.name as template_name,
            COUNT(es.set_id) as total_sets,
            SUM(es.weight * es.reps) as total_volume
        FROM workout_sessions ws
        LEFT JOIN workout_templates wt ON ws.template_id = wt.template_id
        LEFT JOIN exercise_sets es ON ws.session_id = es.session_id
        WHERE ws.user_id = %s
        GROUP BY ws.session_id, ws.session_date, ws.duration_minutes, wt.name
        ORDER BY ws.session_date DESC
        LIMIT %s
        """

        result = execute_query(query, (user_id, limit))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_time_interval(time_range: str) -> str:
    """
    Convert a time range string to a SQL interval expression
    """
    if time_range == "week":
        return "1 WEEK"
    elif time_range == "month":
        return "1 MONTH"
    elif time_range == "quarter":
        return "3 MONTH"
    elif time_range == "half_year":
        return "6 MONTH"
    elif time_range == "year":
        return "1 YEAR"
    else:
        return "1 YEAR"  # Default to 1 year

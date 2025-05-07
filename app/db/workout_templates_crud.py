import mysql.connector
from typing import List, Dict, Any
import traceback
import sys
from app.models.workout_templates import WorkoutTemplateCreate, TemplateExerciseCreate
from app.db.db_connector import get_db_connection # Assuming a db_connector.py for connection pooling
from datetime import datetime

def create_workout_template(
    db: mysql.connector.MySQLConnection,
    template_data: WorkoutTemplateCreate,
    user_id: int
) -> Dict[str, Any]:
    cursor = db.cursor(dictionary=True)

    try:
        print(f"Creating template with name: {template_data.name}, user_id: {user_id}")
        print(f"Exercises count: {len(template_data.exercises)}")

        # Insert into workout_templates table
        template_query = """
        INSERT INTO workout_templates (user_id, name, description)
        VALUES (%s, %s, %s)
        """
        cursor.execute(template_query, (user_id, template_data.name, template_data.description))
        template_id = cursor.lastrowid

        print(f"Created template_id: {template_id}")

        created_exercises_data = []
        # Insert into template_exercises table
        exercise_query = """
        INSERT INTO template_exercises (
            template_id, exercise_id, target_sets, target_reps,
            target_weight, rest_seconds, exercise_order
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for i, ex_data in enumerate(template_data.exercises):
            print(f"Processing exercise {i+1}: exercise_id={ex_data.exercise_id}, sets={ex_data.target_sets}, reps_max={ex_data.reps_max}")
            # Using reps_max for target_reps as per earlier decision
            # exercise_order is 0-indexed from the list, DB might prefer 1-indexed if that's the convention
            cursor.execute(exercise_query, (
                template_id,
                ex_data.exercise_id,
                ex_data.target_sets,
                ex_data.reps_max, # Storing reps_max as target_reps
                ex_data.target_weight,
                ex_data.rest_period_seconds,
                i + 1 # exercise_order (1-indexed)
            ))
            template_exercise_id = cursor.lastrowid
            created_exercises_data.append({
                **ex_data.dict(),
                "template_exercise_id": template_exercise_id,
                "template_id": template_id,
                "target_reps": ex_data.reps_max # for consistency in returned data
            })

        db.commit()
        print("Template and exercises committed to database successfully")

        # Fetch the created template to return all fields including timestamps
        cursor.execute("SELECT * FROM workout_templates WHERE template_id = %s", (template_id,))
        created_template = cursor.fetchone()

        if created_template:
            # Convert datetime objects to strings for Pydantic validation
            if isinstance(created_template.get('created_at'), datetime):
                created_template['created_at'] = created_template['created_at'].isoformat()
            if isinstance(created_template.get('updated_at'), datetime):
                created_template['updated_at'] = created_template['updated_at'].isoformat()

            # Combine template data with its exercises for the return value
            # This structure should align with WorkoutTemplateRead Pydantic model
            return {
                **created_template,
                "exercises": created_exercises_data
            }
        return None # Should ideally raise an exception if not found after creation
    except Exception as e:
        db.rollback()
        print(f"Error in create_workout_template: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise
    finally:
        cursor.close()

def get_workout_templates(
    db: mysql.connector.MySQLConnection,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve all workout templates for a specific user, with pagination.

    Args:
        db: Database connection
        user_id: User ID to filter templates by
        limit: Maximum number of templates to return
        offset: Number of templates to skip for pagination

    Returns:
        List of workout template dictionaries
    """
    cursor = db.cursor(dictionary=True)
    templates = []

    try:
        # Get all templates for the user with pagination
        template_query = """
        SELECT * FROM workout_templates
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(template_query, (user_id, limit, offset))
        templates = cursor.fetchall()

        # For each template, get its exercises
        for template in templates:
            # Convert datetime objects to strings for Pydantic validation
            if isinstance(template.get('created_at'), datetime):
                template['created_at'] = template['created_at'].isoformat()
            if isinstance(template.get('updated_at'), datetime):
                template['updated_at'] = template['updated_at'].isoformat()

            exercise_query = """
            SELECT te.*, e.name as exercise_name, e.description as exercise_description,
                   e.equipment_type, mg.name as muscle_group_name
            FROM template_exercises te
            JOIN exercises e ON te.exercise_id = e.exercise_id
            LEFT JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
            WHERE te.template_id = %s
            ORDER BY te.exercise_order
            """
            cursor.execute(exercise_query, (template["template_id"],))
            exercises = cursor.fetchall()
            template["exercises"] = exercises

    except mysql.connector.Error as err:
        print(f"Database error in get_workout_templates: {err}")
        raise
    finally:
        cursor.close()

    return templates

def get_workout_template(
    db: mysql.connector.MySQLConnection,
    template_id: int
) -> Dict[str, Any]:
    """
    Retrieve a specific workout template by ID, including its exercises.

    Args:
        db: Database connection
        template_id: ID of the template to retrieve

    Returns:
        Workout template dictionary with exercises
    """
    cursor = db.cursor(dictionary=True)
    template = None

    try:
        # Get the template
        template_query = "SELECT * FROM workout_templates WHERE template_id = %s"
        cursor.execute(template_query, (template_id,))
        template = cursor.fetchone()

        if template:
            # Convert datetime objects to strings for Pydantic validation
            if isinstance(template.get('created_at'), datetime):
                template['created_at'] = template['created_at'].isoformat()
            if isinstance(template.get('updated_at'), datetime):
                template['updated_at'] = template['updated_at'].isoformat()

            # Get the exercises for this template
            exercise_query = """
            SELECT te.*, e.name as exercise_name, e.description as exercise_description,
                   e.equipment_type, mg.name as muscle_group_name
            FROM template_exercises te
            JOIN exercises e ON te.exercise_id = e.exercise_id
            LEFT JOIN muscle_groups mg ON e.muscle_group_id = mg.muscle_group_id
            WHERE te.template_id = %s
            ORDER BY te.exercise_order
            """
            cursor.execute(exercise_query, (template_id,))
            exercises = cursor.fetchall()
            template["exercises"] = exercises

    except mysql.connector.Error as err:
        print(f"Database error in get_workout_template: {err}")
        raise
    finally:
        cursor.close()

    return template

def delete_workout_template(
    db: mysql.connector.MySQLConnection,
    template_id: int,
    user_id: int = None
) -> bool:
    """
    Delete a workout template and its associated exercises.

    Args:
        db: Database connection
        template_id: ID of the template to delete
        user_id: Optional user ID to verify ownership

    Returns:
        True if deletion was successful, False otherwise
    """
    cursor = db.cursor(dictionary=True)
    success = False

    try:
        # First, check if the template exists and belongs to the user
        if user_id is not None:
            cursor.execute("SELECT user_id FROM workout_templates WHERE template_id = %s", (template_id,))
            template = cursor.fetchone()

            if not template or template['user_id'] != user_id:
                return False

        # Delete exercises first (foreign key constraint)
        cursor.execute("DELETE FROM template_exercises WHERE template_id = %s", (template_id,))

        # Then delete the template
        cursor.execute("DELETE FROM workout_templates WHERE template_id = %s", (template_id,))

        # Check if any rows were affected
        if cursor.rowcount > 0:
            success = True

        db.commit()

    except mysql.connector.Error as err:
        db.rollback()
        print(f"Database error in delete_workout_template: {err}")
        raise
    finally:
        cursor.close()

    return success

def update_workout_template(
    db: mysql.connector.MySQLConnection,
    template_id: int,
    template_data: dict,
    user_id: int = None
) -> Dict[str, Any]:
    """
    Update a workout template and its associated exercises.

    Args:
        db: Database connection
        template_id: ID of the template to update
        template_data: Dictionary containing updated template data
        user_id: Optional user ID to verify ownership

    Returns:
        Updated template dictionary or None if update failed
    """
    cursor = db.cursor(dictionary=True)
    updated_template = None

    try:
        # First, check if the template exists and belongs to the user
        if user_id is not None:
            cursor.execute("SELECT user_id FROM workout_templates WHERE template_id = %s", (template_id,))
            template = cursor.fetchone()

            if not template or template['user_id'] != user_id:
                return None

        # Update the template
        template_query = """
        UPDATE workout_templates
        SET name = %s, description = %s, updated_at = CURRENT_TIMESTAMP
        WHERE template_id = %s
        """
        cursor.execute(template_query, (
            template_data.get('name'),
            template_data.get('description'),
            template_id
        ))

        # Handle exercises - we'll delete and recreate for simplicity
        if 'exercises' in template_data:
            # Delete existing exercises
            cursor.execute("DELETE FROM template_exercises WHERE template_id = %s", (template_id,))

            # Insert new exercises
            exercise_query = """
            INSERT INTO template_exercises (
                template_id, exercise_id, target_sets, target_reps,
                target_weight, rest_seconds, exercise_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            for i, ex_data in enumerate(template_data['exercises']):
                # Use reps_max for target_reps if available
                target_reps = ex_data.get('reps_max', ex_data.get('target_reps', 0))

                cursor.execute(exercise_query, (
                    template_id,
                    ex_data.get('exercise_id'),
                    ex_data.get('target_sets', 0),
                    target_reps,
                    ex_data.get('target_weight'),
                    ex_data.get('rest_period_seconds', ex_data.get('rest_seconds', 60)),
                    i + 1  # exercise_order (1-indexed)
                ))

        db.commit()

        # Fetch the updated template for return
        updated_template = get_workout_template(db, template_id)

    except mysql.connector.Error as err:
        db.rollback()
        print(f"Database error in update_workout_template: {err}")
        raise
    finally:
        cursor.close()

    return updated_template

# We might need a db_connector.py file if it doesn't exist.
# For now, I'm assuming it provides a get_db_connection() function.
# Example content for app/db/db_connector.py:
# import mysql.connector
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# def get_db_connection():
#     try:
#         conn = mysql.connector.connect(
#             host=os.getenv("MYSQL_HOST"),
#             user=os.getenv("MYSQL_USER"),
#             password=os.getenv("MYSQL_PASSWORD"),
#             database=os.getenv("MYSQL_DATABASE")
#         )
#         return conn
#     except mysql.connector.Error as err:
#         print(f"Error connecting to MySQL: {err}")
#         # In a real app, you might want to raise this or handle it more gracefully
#         return None

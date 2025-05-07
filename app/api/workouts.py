from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
import mysql.connector
import traceback
import sys

# Import new Pydantic models
from app.models.workout_templates import WorkoutTemplateCreate, WorkoutTemplateRead, TemplateExerciseCreate, TemplateExerciseRead
# Import new CRUD function and DB connection
from app.db.workout_templates_crud import (
    create_workout_template as crud_create_workout_template,
    get_workout_templates as crud_get_workout_templates,
    get_workout_template as crud_get_workout_template,
    delete_workout_template as crud_delete_workout_template,
    update_workout_template as crud_update_workout_template
)
from app.db.db_connector import get_db_connection

# Placeholder for authentication dependency - to be implemented/verified later
# from app.api.dependencies import get_current_active_user # Example path
# from app.models.users import User # Example path

router = APIRouter()

@router.post("/", response_model=WorkoutTemplateRead, status_code=201)
async def create_new_workout_template(
    template_in: WorkoutTemplateCreate = Body(...),
    # current_user: User = Depends(get_current_active_user) # TODO: Implement/Uncomment for auth
    # For now, let's simulate a user_id, replace with auth later
    user_id_placeholder: int = 1 # TEMPORARY - REMOVE AND USE AUTHENTICATED USER
):
    """
    Create a new workout template with exercises.
    Uses the new CRUD operations and Pydantic models.
    """
    db_conn = None
    try:
        print(f"Received workout template data: {template_in.dict()}")
        db_conn = get_db_connection()
        if db_conn is None:
            raise HTTPException(status_code=503, detail="Database connection could not be established.")

        # For now, using placeholder user_id. Replace with current_user.user_id when auth is ready
        created_template_dict = crud_create_workout_template(db=db_conn, template_data=template_in, user_id=user_id_placeholder)

        if not created_template_dict:
            raise HTTPException(status_code=500, detail="Failed to create workout template in DB.")

        # Convert the dictionary returned by CRUD to the Pydantic response model
        # This assumes crud_create_workout_template returns a dict compatible with WorkoutTemplateRead
        return WorkoutTemplateRead(**created_template_dict)

    except mysql.connector.Error as db_err: # Specific MySQL errors
        # Log the error for debugging
        error_details = f"Database error: {str(db_err)}"
        print(error_details, file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_details)
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        # Log the error for debugging
        error_details = f"Unexpected error: {str(e)}"
        print(error_details, file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_details)
    finally:
        if db_conn and db_conn.is_connected():
            db_conn.close()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_workout_templates(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # current_user: User = Depends(get_current_active_user) # TODO: Implement/Uncomment for auth
    # For now, let's simulate a user_id, replace with auth later
    user_id_placeholder: int = 1 # TEMPORARY - REMOVE AND USE AUTHENTICATED USER
):
    """
    Get all workout templates for a user
    """
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn is None:
            raise HTTPException(status_code=503, detail="Database connection could not be established.")

        # For now, using placeholder user_id. Replace with current_user.user_id when auth is ready
        templates = crud_get_workout_templates(
            db=db_conn,
            user_id=user_id_placeholder,
            limit=limit,
            offset=offset
        )

        return templates
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database operational error: {db_err}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if db_conn and db_conn.is_connected():
            db_conn.close()

@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_workout_template(
    template_id: int,
    # current_user: User = Depends(get_current_active_user) # TODO: Implement/Uncomment for auth
):
    """
    Get a specific workout template by ID, including its exercises
    """
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn is None:
            raise HTTPException(status_code=503, detail="Database connection could not be established.")

        template = crud_get_workout_template(db=db_conn, template_id=template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Workout template not found")

        # In a real app with authentication, check if the template belongs to the current user
        # if template["user_id"] != current_user.user_id:
        #     raise HTTPException(status_code=403, detail="Not authorized to access this template")

        return template
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database operational error: {db_err}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if db_conn and db_conn.is_connected():
            db_conn.close()

@router.delete("/{template_id}")
async def delete_workout_template(
    template_id: int,
    # current_user: User = Depends(get_current_active_user) # TODO: Implement/Uncomment for auth
    # For now, let's simulate a user_id, replace with auth later
    user_id_placeholder: int = 1 # TEMPORARY - REMOVE AND USE AUTHENTICATED USER
):
    """
    Delete a workout template and its associated exercises
    """
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn is None:
            raise HTTPException(status_code=503, detail="Database connection could not be established.")

        # For now, using placeholder user_id. Replace with current_user.user_id when auth is ready
        success = crud_delete_workout_template(
            db=db_conn,
            template_id=template_id,
            user_id=user_id_placeholder
        )

        if not success:
            raise HTTPException(status_code=404, detail="Workout template not found or you don't have permission to delete it")

        return {"status": "success", "message": "Workout template deleted successfully"}
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database operational error: {db_err}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if db_conn and db_conn.is_connected():
            db_conn.close()

@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_workout_template(
    template_id: int,
    template_data: Dict[str, Any] = Body(...),
    # current_user: User = Depends(get_current_active_user) # TODO: Implement/Uncomment for auth
    # For now, let's simulate a user_id, replace with auth later
    user_id_placeholder: int = 1 # TEMPORARY - REMOVE AND USE AUTHENTICATED USER
):
    """
    Update a workout template and its associated exercises
    """
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn is None:
            raise HTTPException(status_code=503, detail="Database connection could not be established.")

        # For now, using placeholder user_id. Replace with current_user.user_id when auth is ready
        updated_template = crud_update_workout_template(
            db=db_conn,
            template_id=template_id,
            template_data=template_data,
            user_id=user_id_placeholder
        )

        if not updated_template:
            raise HTTPException(status_code=404, detail="Workout template not found or you don't have permission to update it")

        return updated_template
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database operational error: {db_err}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if db_conn and db_conn.is_connected():
            db_conn.close()

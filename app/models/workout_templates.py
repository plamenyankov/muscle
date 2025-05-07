from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TemplateExerciseBase(BaseModel):
    exercise_id: int
    target_sets: int
    reps_min: Optional[int] = None
    reps_max: int
    target_weight: Optional[float] = None
    rest_period_seconds: Optional[int] = None
    exercise_order: Optional[int] = None # Will be set by backend based on list order

class TemplateExerciseCreate(TemplateExerciseBase):
    pass

class TemplateExerciseRead(TemplateExerciseBase):
    template_exercise_id: int
    template_id: int
    # We'll store reps_max in target_reps in DB for now
    target_reps: int # This will represent reps_max from input or an average

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic V2

class WorkoutTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkoutTemplateCreate(WorkoutTemplateBase):
    exercises: List[TemplateExerciseCreate]

class WorkoutTemplateRead(WorkoutTemplateBase):
    template_id: int
    user_id: int
    exercises: List[TemplateExerciseRead]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic V2

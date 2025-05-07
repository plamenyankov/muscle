from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from app.db.connection import execute_query

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key_for_development")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Router
router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

# Models
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    created_at: str

class UserInDB(User):
    password_hash: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    query = "SELECT * FROM users WHERE username = %s"
    results = execute_query(query, (username,))
    if results:
        return results[0]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    """
    Register a new user
    """
    # Check if username or email already exists
    check_query = "SELECT * FROM users WHERE username = %s OR email = %s"
    existing_user = execute_query(check_query, (user.username, user.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Insert the new user
    insert_query = """
    INSERT INTO users (username, email, password_hash, first_name, last_name)
    VALUES (%s, %s, %s, %s, %s)
    """

    try:
        user_id = execute_query(
            insert_query,
            (user.username, user.email, hashed_password, user.first_name, user.last_name),
            fetch=False
        )

        # Get the created user
        created_user = execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return created_user[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and provide access token
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "id": user["user_id"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get information about the current authenticated user
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user(
    user_update: UserBase,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user information
    """
    # Check if updating to an already taken username or email
    if user_update.username != current_user["username"] or user_update.email != current_user["email"]:
        check_query = "SELECT * FROM users WHERE (username = %s OR email = %s) AND user_id != %s"
        existing_user = execute_query(check_query, (user_update.username, user_update.email, current_user["user_id"]))

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already taken"
            )

    # Update user information
    update_query = """
    UPDATE users
    SET username = %s, email = %s, first_name = %s, last_name = %s
    WHERE user_id = %s
    """

    try:
        execute_query(
            update_query,
            (user_update.username, user_update.email, user_update.first_name, user_update.last_name, current_user["user_id"]),
            fetch=False
        )

        # Get the updated user
        updated_user = execute_query("SELECT * FROM users WHERE user_id = %s", (current_user["user_id"],))
        return updated_user[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.put("/me/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password
    """
    # Verify old password
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Hash the new password
    hashed_password = get_password_hash(new_password)

    # Update password
    update_query = "UPDATE users SET password_hash = %s WHERE user_id = %s"

    try:
        execute_query(update_query, (hashed_password, current_user["user_id"]), fetch=False)
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

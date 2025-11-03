# database/auth_db.py

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean  
from sqlalchemy.sql import func
from dotenv import load_dotenv
from database.db import db 
from cachetools import TTLCache
import traceback
from datetime import datetime, timedelta  # <-- FIX: Import timedelta
from utils.colored_logger import logger

# Define a cache for the auth tokens and api_key with a max size and a 30-second TTL
auth_cache = TTLCache(maxsize=1024, ttl=30)
api_key_cache = TTLCache(maxsize=1024, ttl=30)

load_dotenv()

# Try multiple environment variable names for database URL (with and without db_ prefix)
DATABASE_URL = (
    os.environ.get('POSTGRES_URL') or 
    os.environ.get('db_POSTGRES_URL') or 
    os.environ.get('POSTGRES_PRISMA_URL') or 
    os.environ.get('db_POSTGRES_PRISMA_URL') or 
    os.environ.get('db_DATABASE_URL') or 
    os.environ.get('DATABASE_URL') or 
    'sqlite:///tmp/algo.db'  # Use /tmp for serverless fallback
)

logger.database(f"Auth DB using: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=50,  # Increase pool size
        max_overflow=100,  # Increase overflow
        pool_timeout=10  # Increase timeout to 10 seconds
    )
    
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base = declarative_base()
    Base.query = db_session.query_property()
    
    logger.success(f"Database engine created successfully for: {DATABASE_URL}")
except Exception as e:
    logger.error(f"ERROR creating database engine: {str(e)}")
    traceback.print_exc()
    raise

class Auth(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    auth = Column(Text, nullable=False)  # Changed from String(1000) to Text for larger tokens
    is_revoked = Column(Boolean, default=False)  
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class AuthTokens(Base):
    __tablename__ = 'auth_tokens'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    feed_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class ApiKeys(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)
    api_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

# Users table for multi-user support
class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(255), unique=True, nullable=False)
    apikey = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_start_date = Column(DateTime(timezone=True), nullable=True)
    approved_expiry_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

def init_db():
    logger.database("Initializing Auth DB")
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("Database tables created successfully")
    except Exception as e:
        logger.error(f"ERROR initializing database: {str(e)}")
        traceback.print_exc()
        raise

def upsert_auth(name, auth_token, revoke=False):
    """Store or update authentication token for a user"""
    if not name:
        logger.error(f"ERROR in upsert_auth: Empty username")
        return None
        
    if not auth_token and not revoke:
        logger.error(f"ERROR in upsert_auth: Empty auth token for user: {name}")
        return None
    
    logger.info(f"Upserting auth token for user: {name}, token length: {len(auth_token) if auth_token else 0}, revoke: {revoke}")
    
    try:
        auth_obj = Auth.query.filter_by(name=name).first()
        
        if auth_obj:
            # Update existing auth object
            auth_obj.auth = auth_token
            auth_obj.is_revoked = revoke
            print(f"Updating existing auth record for {name} (ID: {auth_obj.id})")
        else:
            # Create new auth object
            auth_obj = Auth(name=name, auth=auth_token, is_revoked=revoke)
            db_session.add(auth_obj)
            print(f"Creating new auth record for {name}")
        
        db_session.commit()
        print(f"Successfully upserted auth token for {name}, ID: {auth_obj.id}")
        
        # Clear cache
        cache_key = f"auth-{name}"
        if cache_key in auth_cache:
            del auth_cache[cache_key]
            
        return auth_obj.id
        
    except Exception as e:
        db_session.rollback()
        print(f"ERROR in upsert_auth: {str(e)}")
        traceback.print_exc()
        return None

def get_auth_token(name):
    """Get authentication token for a user, using cache when available"""
    if not name:
        print(f"ERROR in get_auth_token: Empty username")
        return None
        
    cache_key = f"auth-{name}"
    
    if cache_key in auth_cache:
        auth_obj = auth_cache[cache_key]
        # Ensure that auth_obj is an instance of Auth, not a string
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            return auth_obj.auth
        else:
            del auth_cache[cache_key]  # Remove invalid cache entry
            return None
    else:
        auth_obj = get_auth_token_dbquery(name)
        if isinstance(auth_obj, Auth) and not auth_obj.is_revoked:
            auth_cache[cache_key] = auth_obj  # Store the Auth object, not the string
            return auth_obj.auth
        return None

def get_auth_token_dbquery(name):
    """Query database directly for auth token"""
    if not name:
        print(f"ERROR in get_auth_token_dbquery: Empty username")
        return None
        
    try:
        auth_obj = Auth.query.filter_by(name=name).first()
        if auth_obj and not auth_obj.is_revoked:
            print(f"Successfully fetched auth token for {name} from database")
            return auth_obj  # Return the Auth object
        else:
            print(f"No valid auth token found for name '{name}'.")
            return None
    except Exception as e:
        print(f"ERROR while querying the database for auth token: {str(e)}")
        traceback.print_exc()
        return None

def upsert_api_key(user_id, api_key):
    """Store or update API key for a user"""
    if not user_id:
        print("ERROR in upsert_api_key: user_id is empty")
        return None
        
    if not api_key:
        print(f"ERROR in upsert_api_key: api_key is empty for user_id: {user_id}")
        return None
    
    try:
        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        
        if api_key_obj:
            api_key_obj.api_key = api_key
            print(f"Updating existing API key for user_id: {user_id}")
        else:
            api_key_obj = ApiKeys(user_id=user_id, api_key=api_key)
            db_session.add(api_key_obj)
            print(f"Creating new API key for user_id: {user_id}")
            
        db_session.commit()
        
        # Clear cache
        cache_key = f"api-key-{user_id}"
        if cache_key in api_key_cache:
            del api_key_cache[cache_key]
            
        return api_key_obj.id
        
    except Exception as e:
        db_session.rollback()
        print(f"ERROR in upsert_api_key: {str(e)}")
        traceback.print_exc()
        return None

def get_api_key(user_id):
    """Get API key for a user, using cache when available"""
    if not user_id:
        print("ERROR in get_api_key: user_id is empty")
        return None
        
    cache_key = f"api-key-{user_id}"
    
    if cache_key in api_key_cache:
        print(f"Cache hit for {cache_key}.")
        return api_key_cache[cache_key]
    else:
        api_key_obj = get_api_key_dbquery(user_id)
        if api_key_obj is not None:
            api_key_cache[cache_key] = api_key_obj
        return api_key_obj

def get_api_key_dbquery(user_id):
    """Query database directly for API key"""
    if not user_id:
        print("ERROR in get_api_key_dbquery: user_id is empty")
        return None
        
    try:
        api_key_obj = ApiKeys.query.filter_by(user_id=user_id).first()
        if api_key_obj:
            print(f"Successfully fetched API key for user_id: {user_id} from database")
            return api_key_obj.api_key
        else:
            print(f"No API key found for user_id '{user_id}'.")
            return None
    except Exception as e:
        print(f"ERROR while querying the database for API key: {str(e)}")
        traceback.print_exc()
        return None

def validate_api_key(api_key):
    """Validate API key and return user_id if valid"""
    if not api_key:
        print("ERROR in validate_api_key: api_key is empty")
        return None
        
    try:
        api_key_obj = ApiKeys.query.filter_by(api_key=api_key).first()
        if api_key_obj:
            print(f"Valid API key found for user_id: {api_key_obj.user_id}")
            return api_key_obj.user_id
        else:
            print(f"Invalid API key: {api_key}")
            return None
    except Exception as e:
        print(f"ERROR while validating API key: {str(e)}")
        traceback.print_exc()
        return None

# User management functions

def create_user(username, user_id, apikey, is_admin=False):
    """Create a new user in the database"""
    if not username or not user_id or not apikey:
        print("ERROR in create_user: Missing required fields")
        return {"status": "error", "message": "All fields are required"}
    
    try:
        # Check if username already exists
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            print(f"ERROR in create_user: Username {username} already exists")
            return {"status": "error", "message": "Username already exists"}
            
        # Check if user_id already exists
        existing_id = Users.query.filter_by(user_id=user_id).first()
        if existing_id:
            print(f"ERROR in create_user: User ID {user_id} already exists")
            return {"status": "error", "message": "User ID already exists"}
        
        # Create new user
        user = Users(username=username, user_id=user_id, apikey=apikey, is_admin=is_admin)
        db_session.add(user)
        
        # Also add to ApiKeys table
        api_key = ApiKeys(user_id=user_id, api_key=apikey)
        db_session.add(api_key)
        
        db_session.commit()
        print(f"Successfully created user: {username}")
        return {"status": "success", "message": "User created successfully"}
    except Exception as e:
        db_session.rollback()
        print(f"ERROR creating user: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}

def get_user_by_username(username):
    """Get user details by username"""
    if not username:
        print("ERROR in get_user_by_username: username is empty")
        return None
        
    try:
        user = Users.query.filter_by(username=username).first()
        if user:
            print(f"Successfully fetched user by username: {username}")
            return user
        else:
            print(f"User not found with username: {username}")
            return None
    except Exception as e:
        print(f"ERROR getting user by username: {str(e)}")
        traceback.print_exc()
        return None

def get_user_by_id(user_id):
    """Get user details by user_id"""
    if not user_id:
        print("ERROR in get_user_by_id: user_id is empty")
        return None
        
    try:
        user = Users.query.filter_by(user_id=user_id).first()
        if user:
            print(f"Successfully fetched user by user_id: {user_id}")
            return user
        else:
            print(f"User not found with user_id: {user_id}")
            return None
    except Exception as e:
        print(f"ERROR getting user by user_id: {str(e)}")
        traceback.print_exc()
        return None

def get_all_users():
    """Get all users from the database"""
    try:
        users = Users.query.all()
        print(f"Successfully fetched {len(users)} users")
        return users
    except Exception as e:
        print(f"ERROR getting all users: {str(e)}")
        traceback.print_exc()
        return []

def update_user(username, new_data):
    """Update user details"""
    if not username:
        print("ERROR in update_user: username is empty")
        return {"status": "error", "message": "Username is required"}
        
    if not new_data:
        print("ERROR in update_user: new_data is empty")
        return {"status": "error", "message": "No data to update"}
    
    try:
        user = Users.query.filter_by(username=username).first()
        if not user:
            print(f"ERROR in update_user: User {username} not found")
            return {"status": "error", "message": "User not found"}
        
        # Update user fields if provided in new_data
        if 'user_id' in new_data:
            # Check if new user_id already exists
            existing = Users.query.filter_by(user_id=new_data['user_id']).first()
            if existing and existing.username != username:
                print(f"ERROR in update_user: User ID {new_data['user_id']} already exists")
                return {"status": "error", "message": "User ID already exists"}
            user.user_id = new_data['user_id']
            
        if 'apikey' in new_data:
            user.apikey = new_data['apikey']
            
            # Also update in ApiKeys table
            api_key_obj = ApiKeys.query.filter_by(user_id=user.user_id).first()
            if api_key_obj:
                api_key_obj.api_key = new_data['apikey']
            else:
                api_key_obj = ApiKeys(user_id=user.user_id, api_key=new_data['apikey'])
                db_session.add(api_key_obj)
        
        # Handle approval fields
        if 'is_approved' in new_data:
            user.is_approved = new_data['is_approved']
            
        if 'approved_start_date' in new_data:
            user.approved_start_date = new_data['approved_start_date']
            
        if 'approved_expiry_date' in new_data:
            user.approved_expiry_date = new_data['approved_expiry_date']
            
        if 'is_admin' in new_data:
            user.is_admin = new_data['is_admin']
            
        db_session.commit()
        print(f"Successfully updated user: {username}")
        return {"status": "success", "message": "User updated successfully"}
    except Exception as e:
        db_session.rollback()
        print(f"ERROR updating user: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}

def approve_user(username, duration_days):
    """Approve a user for a specific duration"""
    if not username:
        print("ERROR in approve_user: username is empty")
        return {"status": "error", "message": "Username is required"}
    
    if not isinstance(duration_days, int) or duration_days <= 0:
        print(f"ERROR in approve_user: Invalid duration: {duration_days}")
        return {"status": "error", "message": "Duration must be a positive integer"}
    
    try:
        user = Users.query.filter_by(username=username).first()
        if not user:
            print(f"ERROR in approve_user: User {username} not found")
            return {"status": "error", "message": "User not found"}
        
        # Set approval status and dates
        start_date = datetime.now()
        expiry_date = start_date + timedelta(days=duration_days)
        
        user.is_approved = True
        user.approved_start_date = start_date
        user.approved_expiry_date = expiry_date
        
        db_session.commit()
        
        print(f"Successfully approved user {username} for {duration_days} days (until {expiry_date})")
        return {
            "status": "success", 
            "message": f"User approved for {duration_days} days",
            "expiry_date": expiry_date
        }
    except Exception as e:
        db_session.rollback()
        print(f"ERROR approving user: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}

def check_user_approval(username):
    """Check if a user is approved and the approval is not expired - ADMIN APPROVAL DISABLED"""
    if not username:
        print("ERROR in check_user_approval: username is empty")
        return {"is_valid": False, "message": "Username is required"}
    
    try:
        user = Users.query.filter_by(username=username).first()
        if not user:
            print(f"ERROR in check_user_approval: User {username} not found")
            return {"is_valid": False, "message": "User not found"}
        
        # ADMIN APPROVAL FEATURE DISABLED - All registered users are automatically approved
        print(f"User {username} automatically approved (admin approval disabled)")
        return {
            "is_valid": True, 
            "message": "User automatically approved (admin approval disabled)"
        }
    except Exception as e:
        print(f"ERROR checking user approval: {str(e)}")
        traceback.print_exc()
        return {"is_valid": False, "message": f"Error checking approval status: {str(e)}"}

def delete_user(username):
    """Delete a user from the database"""
    if not username:
        print("ERROR in delete_user: username is empty")
        return {"status": "error", "message": "Username is required"}
    
    try:
        user = Users.query.filter_by(username=username).first()
        if not user:
            print(f"ERROR in delete_user: User {username} not found")
            return {"status": "error", "message": "User not found"}
        
        # Delete related auth tokens
        auth = Auth.query.filter_by(name=username).first()
        if auth:
            db_session.delete(auth)
            print(f"Deleted auth token for user: {username}")
        
        # Delete related API keys
        api_key = ApiKeys.query.filter_by(user_id=user.user_id).first()
        if api_key:
            db_session.delete(api_key)
            print(f"Deleted API key for user: {username}")
        
        # Delete the user
        db_session.delete(user)
        db_session.commit()
        
        print(f"Successfully deleted user: {username}")
        return {"status": "success", "message": "User deleted successfully"}
    except Exception as e:
        db_session.rollback()
        print(f"ERROR deleting user: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}

# Auth Tokens Management Functions
def store_auth_tokens(username, user_id, access_token, feed_token, refresh_token=None, expires_at=None):
    """Store or update auth tokens for a user"""
    try:
        # Check if tokens already exist for this user
        existing_token = AuthTokens.query.filter_by(username=username).first()
        
        if existing_token:
            # Update existing tokens
            existing_token.access_token = access_token
            existing_token.feed_token = feed_token
            existing_token.refresh_token = refresh_token
            existing_token.expires_at = expires_at
            existing_token.is_active = True
            existing_token.updated_at = datetime.now()
            print(f"Updated auth tokens for user: {username}")
        else:
            # Create new token record
            new_token = AuthTokens(
                username=username,
                user_id=user_id,
                access_token=access_token,
                feed_token=feed_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                is_active=True
            )
            db_session.add(new_token)
            print(f"Created new auth tokens for user: {username}")
        
        db_session.commit()
        return {"status": "success", "message": "Auth tokens stored successfully"}
        
    except Exception as e:
        db_session.rollback()
        print(f"ERROR storing auth tokens: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}

def get_auth_tokens(username):
    """Get auth tokens for a user"""
    try:
        token_record = AuthTokens.query.filter_by(username=username, is_active=True).first()
        
        if token_record:
            return {
                "status": "success",
                "access_token": token_record.access_token,
                "feed_token": token_record.feed_token,
                "refresh_token": token_record.refresh_token,
                "expires_at": token_record.expires_at,
                "created_at": token_record.created_at
            }
        else:
            return {"status": "error", "message": "No active tokens found for user"}
            
    except Exception as e:
        print(f"ERROR getting auth tokens: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": f"Database error: {str(e)}"}
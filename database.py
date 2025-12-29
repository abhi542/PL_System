"""
Database Configuration Module
Handles MongoDB Atlas connection and collection management
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """
    Manages MongoDB Atlas connection and provides collection access
    """
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """
        Establish connection to MongoDB Atlas
        """
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            database_name = os.getenv('DATABASE_NAME', 'pl_request_system')
            
            if not mongodb_uri:
                raise ValueError("MONGODB_URI not found in environment variables")
            
            # Create MongoDB client with timeout
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[database_name]
            self.connected = True
            
            # Create indexes for better performance
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.connected = False
            raise Exception(f"Failed to connect to MongoDB Atlas: {str(e)}")
        except Exception as e:
            self.connected = False
            raise Exception(f"Database configuration error: {str(e)}")
    
    def _create_indexes(self):
        """
        Create necessary indexes for collections
        """
        try:
            # Unique index on pl_no in products collection
            self.db.products.create_index('pl_no', unique=True)
            
            # Compound index on requests collection for efficient queries
            self.db.requests.create_index([('pl_no', 1), ('requested_by', 1)])
            self.db.requests.create_index('request_date')
            self.db.requests.create_index('status')
            self.db.requests.create_index('requested_by_emp_id')
            self.db.requests.create_index('approved_by')
            
            # Unique index on emp_id in users collection
            self.db.users.create_index('emp_id', unique=True)
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {str(e)}")
    
    def get_products_collection(self):
        """
        Returns the products collection
        """
        if not self.connected:
            raise Exception("Database not connected")
        return self.db.products
    
    def get_requests_collection(self):
        """
        Returns the requests collection
        """
        if not self.connected:
            raise Exception("Database not connected")
        return self.db.requests
    
    def get_users_collection(self):
        """
        Returns the users collection
        """
        if not self.connected:
            raise Exception("Database not connected")
        return self.db.users
    
    def close(self):
        """
        Close database connection
        """
        if self.client:
            self.client.close()
            self.connected = False


# Global database instance
_db_instance = None

def get_database():
    """
    Get or create database instance (Singleton pattern)
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConfig()
    return _db_instance

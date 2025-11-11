"""Database models and initialization"""
import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent / "db.sqlite3"


def init_db():
    """Initialize database and create tables if not exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id BIGINT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_registered BOOLEAN DEFAULT 0,
            last_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Registrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meeting_date TEXT NOT NULL,
            status TEXT DEFAULT 'registered',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, meeting_date)
        )
    """)
    
    conn.commit()
    conn.close()


class User:
    """User model"""
    def __init__(self, tg_id: int, first_name: str = None, last_name: str = None, 
                 username: str = None, is_active: bool = True, is_registered: bool = False,
                 last_response: str = None, id: int = None):
        self.id = id
        self.tg_id = tg_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_active = is_active
        self.is_registered = is_registered
        self.last_response = last_response
    
    def __repr__(self):
        return f"<User(tg_id={self.tg_id}, username={self.username})>"


class UserRepository:
    """Repository for user operations"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_user(self, tg_id: int, first_name: str = None, last_name: str = None,
                    username: str = None) -> User:
        """Create new user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (tg_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        """, (tg_id, first_name, last_name, username))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return User(tg_id=tg_id, first_name=first_name, last_name=last_name,
                   username=username, id=user_id)
    
    def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, tg_id, first_name, last_name, username, 
                   is_active, is_registered, last_response
            FROM users WHERE tg_id = ?
        """, (tg_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0], tg_id=row[1], first_name=row[2], last_name=row[3],
                username=row[4], is_active=bool(row[5]), is_registered=bool(row[6]),
                last_response=row[7]
            )
        return None
    
    def update_user(self, tg_id: int, **kwargs):
        """Update user fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        if fields:
            values.append(tg_id)
            query = f"UPDATE users SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE tg_id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def get_all_registered_users(self) -> List[User]:
        """Get all registered and active users"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, tg_id, first_name, last_name, username,
                   is_active, is_registered, last_response
            FROM users WHERE is_registered = 1 AND is_active = 1
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append(User(
                id=row[0], tg_id=row[1], first_name=row[2], last_name=row[3],
                username=row[4], is_active=bool(row[5]), is_registered=bool(row[6]),
                last_response=row[7]
            ))
        
        return users
    
    def get_users_by_response(self, response: str) -> List[User]:
        """Get users by their last response"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, tg_id, first_name, last_name, username,
                   is_active, is_registered, last_response
            FROM users WHERE last_response = ? AND is_registered = 1 AND is_active = 1
        """, (response,))
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append(User(
                id=row[0], tg_id=row[1], first_name=row[2], last_name=row[3],
                username=row[4], is_active=bool(row[5]), is_registered=bool(row[6]),
                last_response=row[7]
            ))
        
        return users


class Registration:
    """Registration model"""
    def __init__(self, user_id: int, meeting_date: str, status: str = "registered", id: int = None):
        self.id = id
        self.user_id = user_id
        self.meeting_date = meeting_date
        self.status = status
    
    def __repr__(self):
        return f"<Registration(user_id={self.user_id}, meeting_date={self.meeting_date})>"


class RegistrationRepository:
    """Repository for registration operations"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_registration(self, user_id: int, meeting_date: str) -> Registration:
        """Create new registration"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO registrations (user_id, meeting_date)
                VALUES (?, ?)
            """, (user_id, meeting_date))
            
            conn.commit()
            reg_id = cursor.lastrowid
            conn.close()
            
            return Registration(user_id=user_id, meeting_date=meeting_date, id=reg_id)
        except sqlite3.IntegrityError:
            # Already registered
            conn.close()
            return None
    
    def get_user_registrations(self, user_id: int) -> List[Registration]:
        """Get all registrations for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, meeting_date, status
            FROM registrations WHERE user_id = ?
            ORDER BY meeting_date
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        registrations = []
        for row in rows:
            registrations.append(Registration(
                id=row[0], user_id=row[1], meeting_date=row[2], status=row[3]
            ))
        
        return registrations
    
    def is_registered(self, user_id: int, meeting_date: str) -> bool:
        """Check if user is registered for specific meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM registrations
            WHERE user_id = ? AND meeting_date = ?
        """, (user_id, meeting_date))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def cancel_registration(self, user_id: int, meeting_date: str) -> bool:
        """Cancel registration"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE registrations SET status = 'cancelled'
            WHERE user_id = ? AND meeting_date = ?
        """, (user_id, meeting_date))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_meeting_registrations(self, meeting_date: str) -> List[tuple]:
        """Get all registrations for a specific meeting with user info"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.tg_id, u.first_name, u.last_name, u.username, r.created_at
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            WHERE r.meeting_date = ? AND r.status = 'registered'
            ORDER BY r.created_at
        """, (meeting_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_all_registrations_with_users(self) -> List[tuple]:
        """Get all registrations with user info"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.tg_id, u.first_name, u.last_name, u.username, 
                   r.meeting_date, r.status, r.created_at
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.meeting_date, r.created_at
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows


# Global repository instances
user_repo = UserRepository()
registration_repo = RegistrationRepository()

# Initialize database on import
init_db()


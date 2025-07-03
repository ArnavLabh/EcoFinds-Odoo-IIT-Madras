from app import create_app, db
from app.models import Complaint, ComplaintHistory
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create new tables
    db.create_all()
    
    # Check if we're using PostgreSQL or SQLite
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        # PostgreSQL specific updates
        try:
            with db.engine.connect() as connection:
                # Check if columns exist before adding them
                result = connection.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='complaint' AND column_name IN ('product_id', 'category')
                """))
                existing_columns = [row[0] for row in result]
                
                if 'product_id' not in existing_columns:
                    connection.execute(text('ALTER TABLE complaint ADD COLUMN product_id INTEGER'))
                if 'category' not in existing_columns:
                    connection.execute(text('ALTER TABLE complaint ADD COLUMN category VARCHAR(50)'))
                
                connection.commit()
                print("PostgreSQL database updated successfully")
                
        except Exception as e:
            print(f"Error updating PostgreSQL database: {e}")
            
    else:
        # SQLite specific updates (for development)
        import sqlite3
        
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add new columns to complaint table
            cursor.execute('ALTER TABLE complaint ADD COLUMN product_id INTEGER')
            cursor.execute('ALTER TABLE complaint ADD COLUMN category VARCHAR(50)')
            
            # Add foreign key constraint
            cursor.execute('''
                CREATE TABLE complaint_new (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER,
                    subject VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    priority VARCHAR(20) DEFAULT 'medium',
                    category VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    due_date DATETIME,
                    assigned_to_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (product_id) REFERENCES product(id),
                    FOREIGN KEY (assigned_to_id) REFERENCES user(id)
                )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
                INSERT INTO complaint_new 
                SELECT id, user_id, product_id, subject, description, status, priority, 
                       category, created_at, updated_at, due_date, assigned_to_id 
                FROM complaint
            ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE complaint')
            cursor.execute('ALTER TABLE complaint_new RENAME TO complaint')
            
            conn.commit()
            print("SQLite database updated successfully")
            
        except Exception as e:
            print(f"Error updating SQLite database: {str(e)}")
            conn.rollback()
            
        finally:
            conn.close()

    print("Database update completed!")

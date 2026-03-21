#!/usr/bin/env python3
"""
Apply database migration for two-tier scoring fields.
"""

import sqlite3
import sys
from pathlib import Path

def apply_migration():
    """Apply the two-tier scoring migration to the database."""
    db_path = "aurora.db"
    migration_path = "backend/db/migrations/20260303173123_add_two_tier_scoring_fields.sql"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return 1
    
    if not Path(migration_path).exists():
        print(f"❌ Migration file not found: {migration_path}")
        return 1
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration already applied
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'ml_score' in columns:
            print("✅ Migration already applied. Columns exist:")
            print("   - ml_score")
            print("   - ai_score")
            print("   - final_score")
            print("   - detection_source")
            print("   - ai_explanation")
            print("   - ai_scene_type")
            print("   - ai_confidence")
            conn.close()
            return 0
        
        print("📋 Applying migration...")
        
        # Read migration SQL
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Execute ALTER TABLE statements one by one
        alter_statements = [
            "ALTER TABLE alerts ADD COLUMN ml_score REAL",
            "ALTER TABLE alerts ADD COLUMN ai_score REAL",
            "ALTER TABLE alerts ADD COLUMN final_score REAL",
            "ALTER TABLE alerts ADD COLUMN detection_source TEXT",
            "ALTER TABLE alerts ADD COLUMN ai_explanation TEXT",
            "ALTER TABLE alerts ADD COLUMN ai_scene_type TEXT",
            "ALTER TABLE alerts ADD COLUMN ai_confidence REAL"
        ]
        
        for i, statement in enumerate(alter_statements, 1):
            print(f"   Executing ALTER TABLE {i}/{len(alter_statements)}...")
            try:
                cursor.execute(statement)
                conn.commit()
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   ⚠️  Column already exists, skipping...")
                else:
                    print(f"   ❌ Error: {e}")
                    raise
        
        # Update existing records
        print("   Updating existing records...")
        try:
            cursor.execute("""
                UPDATE alerts SET 
                    ml_score = risk_score,
                    ai_score = 0.0,
                    final_score = risk_score,
                    detection_source = 'ml',
                    ai_scene_type = 'normal'
                WHERE ml_score IS NULL
            """)
            conn.commit()
            print(f"   Updated {cursor.rowcount} existing records")
        except Exception as e:
            print(f"   ⚠️  Update warning: {e}")
        
        # Create indexes
        print("   Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_final_score ON alerts(final_score)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_detection_source ON alerts(detection_source)")
            conn.commit()
        except Exception as e:
            print(f"   ⚠️  Index warning: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Verify migration
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = ['ml_score', 'ai_score', 'final_score', 'detection_source', 
                      'ai_explanation', 'ai_scene_type', 'ai_confidence']
        
        missing = [col for col in new_columns if col not in columns]
        
        if missing:
            print(f"❌ Migration incomplete. Missing columns: {missing}")
            conn.close()
            return 1
        
        print("✅ Migration applied successfully!")
        print("\nNew columns added:")
        for col in new_columns:
            print(f"   - {col}")
        
        # Show table structure
        print("\n📊 Current alerts table structure:")
        cursor.execute("PRAGMA table_info(alerts)")
        for row in cursor.fetchall():
            print(f"   {row[1]}: {row[2]}")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = apply_migration()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Apply database migration."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from models import AsyncSessionLocal


async def apply_migration():
    """Apply the reconciliation_results migration."""
    migration_file = Path(__file__).parent.parent / "migrations" / "002_update_reconciliation_results.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    # Read migration SQL
    with open(migration_file) as f:
        sql = f.read()

    print(f"📄 Reading migration: {migration_file.name}")

    # Execute migration
    async with AsyncSessionLocal() as session:
        try:
            print("🔄 Applying migration...")

            # Parse SQL into individual statements
            # Remove comments and split by semicolons
            statements = []
            current = []
            in_block = False

            for line in sql.splitlines():
                line = line.strip()

                # Skip comment-only lines
                if line.startswith('--'):
                    continue

                # Check if we're in a CREATE TABLE block
                if 'CREATE TABLE' in line:
                    in_block = True

                current.append(line)

                # End of statement
                if line.endswith(';'):
                    stmt = '\n'.join(current)
                    if stmt.strip() and not stmt.strip().startswith('--'):
                        statements.append(stmt)
                    current = []
                    in_block = False

            # Execute each statement
            for i, statement in enumerate(statements, 1):
                print(f"   Executing statement {i}/{len(statements)}...")
                await session.execute(text(statement))

            await session.commit()
            print("✅ Migration applied successfully!")
            return True

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    sys.exit(0 if success else 1)

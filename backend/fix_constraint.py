import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import sqlalchemy as sa

load_dotenv()
DB_URL = os.environ.get("DATABASE_URL")

async def main():
    engine = create_async_engine(DB_URL, echo=True)
    async with engine.begin() as conn:
        try:
            await conn.execute(sa.text("ALTER TABLE leaves DROP CONSTRAINT IF EXISTS leaves_status_check;"))
            await conn.execute(sa.text("ALTER TABLE leaves ADD CONSTRAINT leaves_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'needs_info'));"))
            print("Successfully updated leaves_status_check constraint!")
        except Exception as e:
            print(f"Error updating constraint: {e}")
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())

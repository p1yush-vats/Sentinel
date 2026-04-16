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
            await conn.execute(sa.text("ALTER TABLE leaves ADD COLUMN medical_certificate TEXT;"))
            print("Column 'medical_certificate' added successfully to 'leaves'.")
        except Exception as e:
            print(f"Error adding column: {e}")
    await engine.dispose()

asyncio.run(main())

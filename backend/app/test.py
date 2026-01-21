import asyncio
import asyncpg

async def test():
    try:
        # Try pooler connection
        conn = await asyncpg.connect(
            "postgresql://postgres.jjobzfiwznmascgzvazn:IrgMUYbjfIXxvy7D@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
        )
        print("✅ Pooler connection SUCCESS!")
        await conn.close()
    except Exception as e:
        print(f"❌ Pooler failed: {e}")
        
    try:
        # Try direct connection
        conn = await asyncpg.connect(
            "postgresql://postgres:IrgMUYbjfIXxvy7D@db.jjobzfiwznmascgzvazn.supabase.co:5432/postgres"
        )
        print("✅ Direct connection SUCCESS!")
        await conn.close()
    except Exception as e:
        print(f"❌ Direct failed: {e}")

asyncio.run(test())
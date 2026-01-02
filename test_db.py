import asyncio
from db import init_session_maker, add_entry, get_entries
from models import JournalEntry

async def main():
    try:
        session_maker = await init_session_maker()
        print("DB Connected")
        
        # Test fetching entries (assuming some exist, or just valid query)
        # using a dummy user_id or 123
        entries = await get_entries(session_maker, 123)
        print(f"Fetched {len(entries)} entries for user 123")
        for e in entries:
            print(f"- {e.emotion} at {e.location}")
            
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

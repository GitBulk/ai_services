import asyncio

from tortoise import Tortoise

from app.db.tortoise_config import TORTOISE_CONFIG


async def main():
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas(safe=True)
    print("[OK] users table created (safe=True — skipped if already exists)")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())

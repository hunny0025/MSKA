"""
Initialize local PostgreSQL database, creating db, user, schema tables, and seeding standard admin account.
"""

import asyncio
import os
import sys
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select

# Add parent directory to sys.path to enable backend relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.database import Base
from models.user import User
from models.role import Role
from core.permissions import Roles


async def get_admin_connection():
    settings = get_settings()
    
    # Try combinations to connect to admin 'postgres' database
    combos = [
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@localhost:{settings.postgres_port}/postgres",
        f"postgresql+asyncpg://postgres:postgres@localhost:{settings.postgres_port}/postgres",
        f"postgresql+asyncpg://postgres:admin@localhost:{settings.postgres_port}/postgres",
        f"postgresql+asyncpg://postgres@localhost:{settings.postgres_port}/postgres",
    ]
    
    for url in combos:
        try:
            engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"Successfully connected to PostgreSQL administrative console using: {url.split('@')[0]}@...")
            return engine
        except Exception as e:
            print(f"Connection failed for {url.split('@')[0]}: {e}")
            continue

            
    print("Could not connect to PostgreSQL. Please ensure PostgreSQL is running and you have correct credentials in .env")
    sys.exit(1)


async def setup_db_and_user():
    settings = get_settings()
    admin_engine = await get_admin_connection()
    
    async with admin_engine.connect() as conn:
        # Check database
        res = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{settings.postgres_db}'"))
        if not res.scalar():
            print(f"Creating database '{settings.postgres_db}'...")
            await conn.execute(text(f"CREATE DATABASE {settings.postgres_db}"))
            
        # Check user
        res = await conn.execute(text(f"SELECT 1 FROM pg_roles WHERE rolname='{settings.postgres_user}'"))
        if not res.scalar():
            print(f"Creating user '{settings.postgres_user}'...")
            await conn.execute(text(f"CREATE USER {settings.postgres_user} WITH PASSWORD '{settings.postgres_password}'"))
            
        # Grant permissions
        await conn.execute(text(f"GRANT ALL PRIVILEGES ON DATABASE {settings.postgres_db} TO {settings.postgres_user}"))
        try:
            await conn.execute(text(f"ALTER USER {settings.postgres_user} WITH SUPERUSER"))
        except Exception:
            pass
            
    await admin_engine.dispose()


async def create_schema_and_seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        print("Creating tables in application database...")
        await conn.run_sync(Base.metadata.create_all)
        print("Schema created successfully.")
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Seed Roles
        role_res = await session.execute(select(Role).where(Role.name == Roles.PLATFORM_ADMIN))
        admin_role = role_res.scalar_one_or_none()
        
        if not admin_role:
            print("Seeding Roles catalog...")
            roles_to_create = [
                Role(name=Roles.PLATFORM_ADMIN, description="Full platform admin access"),
                Role(name=Roles.DEPARTMENT_LEAD, description="Department Lead access"),
                Role(name=Roles.PROJECT_ADMIN, description="Project Admin access"),
                Role(name=Roles.EMPLOYEE, description="Standard employee access"),
                Role(name=Roles.AUDITOR, description="Compliance Auditor access"),
            ]
            session.add_all(roles_to_create)
            await session.commit()
            
            role_res = await session.execute(select(Role).where(Role.name == Roles.PLATFORM_ADMIN))
            admin_role = role_res.scalar_one()
            
        # Seed Admin User
        user_res = await session.execute(select(User).where(User.username == "admin"))
        admin_user = user_res.scalar_one_or_none()
        
        if not admin_user:
            print("Seeding admin operator (username=admin, password=adminpassword123)...")
            hashed_pwd = bcrypt.hashpw("adminpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                username="admin",
                email="admin@marutisuzuki.com",
                hashed_password=hashed_pwd,
                role_id=admin_role.id
            )
            session.add(admin_user)
            await session.commit()
            print("Default admin operator seeded successfully.")
            
    await engine.dispose()


async def main():
    await setup_db_and_user()
    await create_schema_and_seed()
    print("Database initialization complete! You can run the FastAPI app now.")


if __name__ == "__main__":
    asyncio.run(main())

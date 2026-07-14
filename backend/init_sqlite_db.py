"""
Initialize local SQLite database, creating schemas, seeding roles, and creating admin account.
"""

import asyncio
import os
import sys
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# Add parent directory to sys.path to enable backend relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.database import Base
from models.user import User
from models.role import Role
from core.permissions import Roles


async def init_sqlite():
    settings = get_settings()
    print(f"Connecting to SQLite database at {settings.database_url}...")
    
    engine = create_async_engine(settings.database_url, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        print("Creating SQLite tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("SQLite tables created successfully.")
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Seed Roles
        role_res = await session.execute(select(Role).where(Role.name == Roles.PLATFORM_ADMIN))
        admin_role = role_res.scalar_one_or_none()
        
        if not admin_role:
            print("Seeding standard system Roles...")
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
            print("Seeding admin user (username=admin, password=adminpassword123)...")
            hashed_pwd = bcrypt.hashpw("adminpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                username="admin",
                email="admin@marutisuzuki.com",
                hashed_password=hashed_pwd,
                role_id=admin_role.id
            )
            session.add(admin_user)
            await session.commit()
            print("Admin user seeded successfully!")
            
    await engine.dispose()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(init_sqlite())

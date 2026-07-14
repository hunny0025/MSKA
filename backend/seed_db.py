"""
Lightweight database seed script for production/deployment environments.
Creates initial roles, departments, users (including plat_admin_user), and projects.
Has zero dependencies on external document generation libraries (docx, reportlab, pptx).
"""

import asyncio
import os
import sys
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, insert

# Add current folder to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.database import Base
from core.permissions import Roles
from models.user import User
from models.role import Role
from models.department import Department
from models.project import Project
from models.project import project_users


async def seed_core_data():
    settings = get_settings()
    print(f"Connecting to database at {settings.database_url}...")
    
    engine = create_async_engine(settings.database_url, echo=True)
    
    # Create all tables if they don't exist
    async with engine.begin() as conn:
        print("Ensuring tables exist...")
        await conn.run_sync(Base.metadata.create_all)
        print("Table checking complete.")
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Seed Roles
        role_ids = {}
        for role_name in Roles.ALL:
            role_res = await session.execute(select(Role).where(Role.name == role_name))
            role_obj = role_res.scalar_one_or_none()
            if not role_obj:
                print(f"Seeding Role: {role_name}...")
                role_obj = Role(name=role_name, description=f"{role_name.replace('_', ' ').title()} role access")
                session.add(role_obj)
                await session.flush()
            role_ids[role_name] = role_obj.id

        # 2. Seed Departments
        dept_ids = {}
        depts = ["QA", "PROD", "HR", "ENG", "SUPPLY"]
        for dept_name in depts:
            dept_res = await session.execute(select(Department).where(Department.name == dept_name))
            dept_obj = dept_res.scalar_one_or_none()
            if not dept_obj:
                print(f"Seeding Department: {dept_name}...")
                dept_obj = Department(name=dept_name, description=f"{dept_name} Department")
                session.add(dept_obj)
                await session.flush()
            dept_ids[dept_name] = dept_obj.id

        # 3. Seed Projects
        project_ids = {}
        project_defs = [
            ("proj_qa", "QA Welding Procedures", dept_ids["QA"]),
            ("proj_prod", "Production Supplier Audits", dept_ids["PROD"]),
            ("proj_hr", "HR Records Management", dept_ids["HR"]),
            ("proj_eng", "K15C Engine Development", dept_ids["ENG"]),
            ("proj_safety", "Plant Floor Safety", dept_ids["QA"]),
        ]
        for key, name, dept_id in project_defs:
            proj_res = await session.execute(select(Project).where(Project.name == name))
            proj_obj = proj_res.scalar_one_or_none()
            if not proj_obj:
                print(f"Seeding Project: {name}...")
                proj_obj = Project(name=name, description=f"Project: {name}", department_id=dept_id)
                session.add(proj_obj)
                await session.flush()
            project_ids[key] = proj_obj.id

        # 4. Seed Users
        pwd_hash = bcrypt.hashpw("testpass123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user_ids = {}
        
        user_defs = [
            ("emp_user", "emp@marutisuzuki.com", role_ids[Roles.EMPLOYEE], dept_ids["QA"]),
            ("lead_user", "lead@marutisuzuki.com", role_ids[Roles.DEPARTMENT_LEAD], dept_ids["PROD"]),
            ("proj_admin_user", "projadmin@marutisuzuki.com", role_ids[Roles.PROJECT_ADMIN], dept_ids["ENG"]),
            ("plat_admin_user", "platadmin@marutisuzuki.com", role_ids[Roles.PLATFORM_ADMIN], None),
            ("auditor_user", "auditor@marutisuzuki.com", role_ids[Roles.AUDITOR], None),
            ("outsider_user", "outsider@marutisuzuki.com", role_ids[Roles.EMPLOYEE], dept_ids["HR"]),
        ]
        
        for username, email, role_id, dept_id in user_defs:
            user_res = await session.execute(select(User).where(User.username == username))
            user_obj = user_res.scalar_one_or_none()
            if not user_obj:
                print(f"Seeding User: {username}...")
                user_obj = User(
                    username=username,
                    email=email,
                    hashed_password=pwd_hash,
                    role_id=role_id,
                    department_id=dept_id
                )
                session.add(user_obj)
                await session.flush()
            user_ids[username] = user_obj.id

        # 5. Seed Project Memberships
        memberships = [
            ("emp_user", "proj_qa"),
            ("emp_user", "proj_safety"),
            ("lead_user", "proj_prod"),
            ("proj_admin_user", "proj_eng"),
            ("plat_admin_user", "proj_qa"),
            ("plat_admin_user", "proj_eng"),
            ("auditor_user", "proj_qa"),
            ("outsider_user", "proj_hr"),
        ]
        
        for username, proj_key in memberships:
            uid = user_ids[username]
            pid = project_ids[proj_key]
            
            # Check if mapping exists
            map_res = await session.execute(
                select(project_users).where(
                    project_users.c.user_id == uid,
                    project_users.c.project_id == pid
                )
            )
            if not map_res.scalar_one_or_none():
                print(f"Assigning {username} to {proj_key}...")
                await session.execute(
                    insert(project_users).values(user_id=uid, project_id=pid)
                )

        await session.commit()
    await engine.dispose()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_core_data())

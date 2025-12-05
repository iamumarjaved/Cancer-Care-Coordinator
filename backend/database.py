"""Database setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
import logging

from config import settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()


def get_async_database_url(url: str) -> str:
    """Convert sync database URL to async driver URL."""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("postgres://"):
        # Handle Heroku-style postgres:// URLs
        return url.replace("postgres://", "postgresql+asyncpg://")
    return url


def get_sync_database_url(url: str) -> str:
    """Ensure sync database URL uses correct driver."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://")
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://")
    return url


DATABASE_URL = settings.DATABASE_URL
SYNC_DATABASE_URL = get_sync_database_url(DATABASE_URL)
ASYNC_DATABASE_URL = get_async_database_url(DATABASE_URL)

# Determine database type for connection args
is_sqlite = "sqlite" in DATABASE_URL.lower()

# Sync engine for migrations and testing
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True if not is_sqlite else False,
)

# Async engine for production use
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True if not is_sqlite else False,
)

# Session factories
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Alias for compatibility
async_session_maker = AsyncSessionLocal


async def get_db():
    """FastAPI dependency for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database tables (sync)."""
    from models import db_models  # noqa: F401 - Import to register models
    Base.metadata.create_all(bind=sync_engine)
    logger.info(f"Database initialized at {DATABASE_URL}")


async def init_db_async():
    """Initialize database tables (async)."""
    from models import db_models  # noqa: F401 - Import to register models
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database initialized at {DATABASE_URL}")

    # Seed mock patients if table is empty
    await seed_patients_if_empty()


async def seed_patients_if_empty():
    """Seed patients from JSON file if the table is empty."""
    import json
    from pathlib import Path
    from sqlalchemy import select, func
    from models.db_models import PatientDB

    async with AsyncSessionLocal() as session:
        # Check if patients already exist
        result = await session.execute(select(func.count(PatientDB.id)))
        count = result.scalar()

        if count > 0:
            logger.info(f"Database already has {count} patients, skipping seed")
            return

        # Load from JSON file
        data_path = Path(__file__).parent / "data" / "mock_patients.json"
        try:
            with open(data_path, "r") as f:
                data = json.load(f)

            for patient_data in data.get("patients", []):
                patient_db = PatientDB(
                    id=patient_data["id"],
                    first_name=patient_data["first_name"],
                    last_name=patient_data["last_name"],
                    date_of_birth=patient_data["date_of_birth"],
                    sex=patient_data.get("sex", "Unknown"),
                    email=patient_data.get("email"),
                    phone=patient_data.get("phone"),
                    cancer_details=patient_data.get("cancer_details"),
                    comorbidities=patient_data.get("comorbidities", []),
                    organ_function=patient_data.get("organ_function", []),
                    ecog_status=patient_data.get("ecog_status"),
                    current_medications=patient_data.get("current_medications", []),
                    allergies=patient_data.get("allergies", []),
                    smoking_status=patient_data.get("smoking_status"),
                    pack_years=patient_data.get("pack_years"),
                    genomic_report_id=patient_data.get("genomic_report_id"),
                    clinical_notes=patient_data.get("clinical_notes", [])
                )
                session.add(patient_db)

            await session.commit()
            logger.info(f"Seeded {len(data.get('patients', []))} patients from {data_path}")

        except FileNotFoundError:
            logger.warning(f"Mock data file not found: {data_path}")
        except Exception as e:
            logger.error(f"Error seeding patients: {e}")
            await session.rollback()


@asynccontextmanager
async def get_db_session():
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_session():
    """Get sync database session for testing."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

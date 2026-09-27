from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here so Base.metadata is fully populated
# before Alembic (or create_all) ever looks at it.
from app.models import agent, registration, publication, audit  # noqa: E402,F401
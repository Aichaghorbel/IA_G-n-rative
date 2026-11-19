"""Script to drop all tables and recreate them from scratch based on SQLAlchemy models."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.database import engine, Base
import app.models  # noqa: F401 — registers all models in Base.metadata

print("=" * 60)
print("  DROP ALL TABLES")
print("=" * 60)
Base.metadata.drop_all(bind=engine)
print("[OK] All tables dropped.")

print("=" * 60)
print("  CREATE ALL TABLES (from updated models)")
print("=" * 60)
Base.metadata.create_all(bind=engine)
print("[OK] All tables created.")

# Verify: list all tables
from sqlalchemy import inspect as sa_inspect
inspector = sa_inspect(engine)
tables = inspector.get_table_names()
print(f"\n[INFO] Tables created ({len(tables)}):")
for t in sorted(tables):
    cols = [c["name"] for c in inspector.get_columns(t)]
    fks  = [f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
            for fk in inspector.get_foreign_keys(t)]
    print(f"  {t}: {cols}")
    if fks:
        for fk in fks:
            print(f"    FK: {fk}")

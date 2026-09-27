# intentionally empty — app/db/base.py imports the model modules directly,
# which is what populates Base.metadata. This file just needs to exist
# so "app.models" is a valid package.
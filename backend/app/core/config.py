from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    instance_connection_name: str
    db_user: str
    db_pass: str
    db_name: str

    class Config:
        env_file = ".env"

settings = Settings()
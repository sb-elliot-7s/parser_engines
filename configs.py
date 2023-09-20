from pydantic import BaseSettings


class Configs(BaseSettings):
    base_url: str
    save_dir: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def get_configs() -> Configs:
    return Configs()

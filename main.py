from pydantic import BaseModel, model_validator
from box import Box


class AttrAccessModel(BaseModel):
    """
    Pydantic-модель с доступом к полям через точку.
    Динамические поля разрешены, но оборачиваются в Box (аналог AttrDict).
    """

    class Config:
        extra = 'allow'

    @model_validator(mode="after")
    def _convert(self) -> "AttrAccessModel":
        for key, value in self.__pydantic_extra__.items():
            if isinstance(value, (dict, )):
                self.__dict__[key] = Box(value, default_box=True)
        return self


class KafkaConfig(BaseModel):
    brokers: list[str]  # Валидация вложенных структур


class DBConfig(BaseModel):
    host: str
    port: int = 5432


class Version(BaseModel):
    majority: str
    sub: int = 1


class AppConfig(AttrAccessModel):
    """
    Добавляем проверяемые модели, то есть если с моделью что-то не так, упадем на загрузке.
    Дополнительно имеем возможность создавать произвольные поля
    """
    db: DBConfig  # Валидируемое поле
    kafka: KafkaConfig  # Ещё одно валидируемое поле
    top_version: Version
    # Динамические поля (например, `logging`) тоже разрешены


version = Version(majority="1", sub=2)

# Пример использования
data = {
    "db": {"host": "localhost", "port": 5432},
    "kafka": {"brokers": ["kafka:9092"]},
    "top_version": {"majority": "10", "sub": 15},
    "logging": {
        "handlers": {
            "file": {
                "path": "/var/log",
                "options": {"alignment": "center"},
            },
        },
        "version": version,
        "versions": [version, Version(majority="3"), Version(majority="4")],
        "version2": {"majority": "10", "sub": 15},
        "level": "INFO",
    },
}

config = AppConfig(**data)

# Доступ через точку
assert type(config.db) is DBConfig
assert config.db.host == "localhost"
assert config.db.port == 5432
assert config.kafka.brokers == ["kafka:9092"]

print(type(config.logging.version))  # <class '__main__.Version'>
print(config.logging.version)  # majority='1' sub=2

print(type(config.logging.versions))  # <class 'box.box_list.BoxList'>
print(config.logging.versions)  # [Version(majority='1', sub=2), Version(majority='3', sub=1), Version(majority='4', sub=1)]
print(isinstance(config.logging.versions, list))  # True
print(type(config.logging.versions[1]))  # <class '__main__.Version'>
print(config.logging.versions[1])  # majority='3' sub=1

assert type(config.logging.version2) is Box
assert config.logging.version2.majority == "10"

print(config.logging.handlers.file.path)  # /var/log
print(config.logging.handlers.file.options.rotate)  # {}

print(type(config.logging))  # <class 'box.box.Box'>
print(config.logging.level)  # "INFO"
v = config.logging
v.level = "ERROR"
print(v.level)  # "ERROR"
print(config.logging.level)  # "ERROR"
print(config.top_version.majority)

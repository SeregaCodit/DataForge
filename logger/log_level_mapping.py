from dataclasses import dataclass

@dataclass
class LevelMapping:
    debug: str = 'DEBUG'
    info: str = 'INFO'
    warning: str = 'WARNING'
    error: str = 'ERROR'
    critical: str = 'CRITICAL'

    @classmethod
    def mapping(cls) -> tuple:
        return str(LevelMapping.debug), str(LevelMapping.info), str(LevelMapping.warning), str(LevelMapping.error), str(LevelMapping.critical)

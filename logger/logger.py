import logging
import logging.config
from pathlib import Path
from logger.log_level_mapping import LevelMapping


class LoggerConfigurator:
    @staticmethod
    def setup(name: str, log_path: Path, log_level: str = LevelMapping.info):
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': log_level,
                    'stream': 'ext://sys.stdout',
                },
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['console'],
                    'level': LevelMapping.info,
                    'propagate': True
                },
            }
        }

        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)

            config['handlers']['file'] = {
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'level': LevelMapping.debug,
                'filename': str(log_path),
                'encoding': 'utf8'
            }
            config['loggers']['']['handlers'].append('file')

        logging.config.dictConfig(config)
        return logging.getLogger(name)

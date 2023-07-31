import logging


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(message)s',
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(levelname)s %(message)s',
        },
        'base': {
            'format': (
                '%(asctime)s | '
                '%(levelname)s | '
                '%(name)s - %(module)s | '
                '%(message)s'
            ),
        },

    },

    # 'filters': {
    #     'lowererror': {
    #         'class': 'logging.LowerErrorFilter',
    #     },
    #     'uppererror': {
    #         'class': 'logging.UpperErrorFilter',
    #     },
    # },

    'handlers': {
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            "filename": "config/log/debug.log",
            'maxBytes': 102400,
            'backupCount': 5,
            # 'filters': ['lowererror'],
        },
        'file_handler_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            "filename": "config/log/error.log",
            'maxBytes': 102400,
            'backupCount': 5,
            # 'filters': ['lowererror'],
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'base',
            # 'formatter': 'base',
        },
    },

    'loggers': {
        '': {
            'handlers': ['console'],
            # 'propagate': False,
            'level': 'INFO',
        },
        'app.authorization': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },
    },
}

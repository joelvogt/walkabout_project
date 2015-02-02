client_id = 'osx_client'
modules = dict(
    pixelman_logger = dict(
        buffer_size = 4096,
        connection = 'tcpsock',
        serialization = dict(
            data = 'python_pickling',
            results = 'python_pickling'
        )
    )
)
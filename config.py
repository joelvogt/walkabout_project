client_id = 'osx_client'
modules = dict(
    remote_file=dict(
        buffer_size=12288,
        connection = 'tcpsock',
        serialization = dict(
            data='python_pickling',
            results='python_pickling'
        )
    )
)
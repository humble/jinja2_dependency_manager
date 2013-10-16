import os

def is_debug():
    """Determine whether we're running in the Google AppEngine development environment."""
    software, _version = (os.getenv('SERVER_SOFTWARE') or '/').split('/')
    return (software == 'Development')

"""OS parser limits, installed before importing the PDF library."""
import sys


def isolation_supported():
    return sys.platform.startswith('linux')


def apply_parser_limits():
    if not isolation_supported():
        return False
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    return True

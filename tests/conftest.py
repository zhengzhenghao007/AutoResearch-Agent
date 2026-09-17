"""Legacy provider demos execute on import; exclude unless explicitly opted in."""
LIVE_DEMOS = {'test_reader_pipeline.py', 'test_reader_reflection.py', 'test_reflection.py', 'test_structured_output.py'}


def pytest_addoption(parser):
    parser.addoption('--run-live', action='store_true', default=False,
                     help='Collect legacy live-provider demos (network/API charges possible)')


def pytest_ignore_collect(collection_path, config):
    if collection_path.name in LIVE_DEMOS and not config.getoption('--run-live'):
        return True

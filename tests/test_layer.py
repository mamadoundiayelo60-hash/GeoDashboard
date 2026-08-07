from services.layer_manager import LayerManager


def test_manager():

    manager = LayerManager()

    assert manager.count() == 0
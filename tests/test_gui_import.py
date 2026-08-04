def test_gui_module_imports():
    from areco_planning.gui.app import MainWindow
    assert MainWindow is not None

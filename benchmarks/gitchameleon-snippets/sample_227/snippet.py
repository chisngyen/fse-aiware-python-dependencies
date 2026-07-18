import pytest

@pytest.
hookimpl(hookwrapper=True)
def pytest_runtest_setup():
    yield

# --- test ---
import pluggy

def test_hookwrapper_configuration_with_plugin_manager():
    pm = pluggy.PluginManager("pytest")
    
    class DummyPlugin:
        pytest_runtest_setup = pytest_runtest_setup

    plugin = DummyPlugin()
    pm.register(plugin)
    
    hookimpls = pm.hook.pytest_runtest_setup.get_hookimpls()
    for impl in hookimpls:
        if impl.plugin is plugin:
            opts = impl.opts
            assert opts.get("hookwrapper") is True, "Expected hookwrapper=True for a hook wrapper"
            break
    else:
        pytest.fail("pytest_runtest_setup implementation not found in plugin manager.")


test_hookwrapper_configuration_with_plugin_manager()

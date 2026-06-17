from applypilot.config.settings import Settings


def test_settings_default_to_explicit_safe_runtime_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.debug is False
    assert "*" not in settings.allowed_cors_origins()
    assert "http://localhost:4173" in settings.allowed_cors_origins()
    assert "http://127.0.0.1:4173" in settings.allowed_cors_origins()


def test_settings_add_codespaces_origins_without_losing_local_dev_origins() -> None:
    settings = Settings(_env_file=None)

    origins = settings.allowed_cors_origins(
        codespace_name="applygo-demo",
        codespaces_domain="app.github.dev",
    )

    assert "https://applygo-demo-4173.app.github.dev" in origins
    assert "https://applygo-demo-3000.app.github.dev" in origins
    assert "https://applygo-demo-5173.app.github.dev" in origins
    assert "http://localhost:4173" in origins

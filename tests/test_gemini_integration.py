from app.llm.gemini import answer_with_gemini, model_name


def test_gemini_configuration_defaults_to_requested_model(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert model_name() == "gemini-3.1-flash-lite"


def test_gemini_is_optional_without_an_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert answer_with_gemini("Question", []) is None

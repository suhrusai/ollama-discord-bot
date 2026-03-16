import discord

from bot.utils import fix_codeblocks, map_button_style, safe_json_parse


def test_fix_codeblocks_adds_backticks():
    payload = "\npython\nprint('hi')\n"
    fixed = fix_codeblocks(payload)
    assert "```python" in fixed
    assert fixed.endswith("```")


def test_safe_json_parse_handles_embedded_json():
    payload = "Here is a response: {\"key\": \"value\"}"
    parsed = safe_json_parse(payload)
    assert parsed == {"key": "value"}


def test_safe_json_parse_returns_none_for_invalid():
    assert safe_json_parse("plain text only") is None


def test_map_button_style_defaults_to_primary():
    assert map_button_style("unknown") == discord.ButtonStyle.primary


def test_map_button_style_matches_known_styles():
    assert map_button_style("danger") == discord.ButtonStyle.danger

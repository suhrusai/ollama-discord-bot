import json
import re

import discord

def fix_codeblocks(text):
    """Ensure code fences are well-formed before sending to Discord."""
    languages = ["python", "java", "cpp", "c", "rust", "javascript", "ts"]

    for lang in languages:
        text = re.sub(rf"\n{lang}\n", f"\n```{lang}\n", text)

    if text.count("```") % 2 != 0:
        text += "\n```"

    return text

def safe_json_parse(ai_text):
    """Try to decode JSON output from the model and fall back to heuristic extraction."""
    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", ai_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None

def map_button_style(style):
    styles = {
        "primary": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
    }

    return styles.get(style, discord.ButtonStyle.primary)

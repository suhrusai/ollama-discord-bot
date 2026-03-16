import discord

from bot.utils import fix_codeblocks, map_button_style, safe_json_parse

async def send_ai_json(channel, ai_response):
    parsed = safe_json_parse(ai_response)

    if not parsed:
        await channel.send(ai_response[:2000])
        return

    for msg in parsed.get("messages", []):
        content = fix_codeblocks(msg.get("content", ""))

        if len(content) > 2000:
            content = content[:1990]

        embeds = []
        for embed_payload in msg.get("embeds", []):
            embed = discord.Embed(
                title=embed_payload.get("title"),
                description=embed_payload.get("description"),
                color=embed_payload.get("color", 3447003)
            )

            for field in embed_payload.get("fields", []):
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )

            if "image" in embed_payload:
                embed.set_image(url=embed_payload["image"]["url"])

            if "thumbnail" in embed_payload:
                embed.set_thumbnail(url=embed_payload["thumbnail"]["url"])

            embeds.append(embed)

        view = None
        components = msg.get("components", [])

        if components:
            view = discord.ui.View()
            for row in components:
                for button_payload in row.get("buttons", []):
                    style = button_payload.get("style", "primary")

                    if style == "link":
                        button = discord.ui.Button(
                            label=button_payload.get("label", "Open"),
                            url=button_payload.get("url")
                        )
                    else:
                        button = discord.ui.Button(
                            label=button_payload.get("label", "Click"),
                            custom_id=button_payload.get("custom_id", "btn"),
                            style=map_button_style(style)
                        )

                    view.add_item(button)

        await channel.send(
            content=content,
            embeds=embeds,
            view=view
        )

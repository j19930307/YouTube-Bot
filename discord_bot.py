import json
import os

import requests
from discord import Embed

from discord_message import SnsInfo


class DiscordBot:
    def __init__(self):
        pass

    def send_message(self, discord_channel_id: str, content: str, embeds=None):
        if embeds is None:
            embeds = []
        url = f"https://discord.com/api/channels/{discord_channel_id}/messages"
        data = dict()
        data["content"] = content
        if embeds is not None:
            data["embeds"] = [embed.to_dict() for embed in embeds]
        payload = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bot {os.environ["BOT_TOKEN"]}',
        }

        return requests.request("POST", url, headers=headers, data=payload)

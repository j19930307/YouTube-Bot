import json
import os

import requests
from discord import Embed

from discord_message import SnsInfo


def generate_embeds(sns_info: SnsInfo):
    embeds = []
    # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
    for index, image_url in enumerate(sns_info.images[slice(4)]):
        if index == 0:
            embed = (
                Embed(title=sns_info.title, description=sns_info.content, url=sns_info.post_link,
                      timestamp=sns_info.timestamp).set_author(
                    name=sns_info.profile.name, icon_url=sns_info.profile.url)
                .set_image(url=image_url))
            embeds.append(embed)
        else:
            embeds.append(Embed(url=sns_info.post_link)
                          .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                          .set_image(url=image_url))
    else:
        embeds.append(Embed(title=sns_info.title, description=sns_info.content, url=sns_info.post_link).set_author(
            name=sns_info.profile.name, icon_url=sns_info.profile.url))
    return embeds


def send_message_by_api(discord_channel_id: str, content: str, embeds=None):
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

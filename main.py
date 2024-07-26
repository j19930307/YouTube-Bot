from dotenv import load_dotenv

import discord_bot
import youtube_crawler
from firebase import Firebase

load_dotenv()
firebase = Firebase()

print("開始抓取新影片...")
for channel in firebase.get_channel_list():
    if channel.exists:
        shorts_id = youtube_crawler.get_latest_shorts(channel.id, channel.get("latest_short_id"))
        videos_id = youtube_crawler.get_latest_videos(channel.id, channel.get("latest_video_id"))
        if shorts_id:
            shorts_url = [f"https://youtube.com/shorts/{short_id}" for short_id in shorts_id]
            response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                       content=f'{channel.id}上傳了短影片\n{"\n".join(shorts_url)}')
            if response.status_code == 200:
                print(f"短影片發送到 Discord 頻道成功")
                firebase.set_latest_short_id(channel_handle=channel.id, latest_short_id=shorts_id[0])
            else:
                print(f"短影片發送到 Discord 頻道失敗")
        else:
            print(f"沒有新短影片")
        if videos_id:
            videos_url = [f"https://youtu.be/{video_id}" for video_id in videos_id]
            response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                       content=f'{channel.id}上傳了影片\n{"\n".join(videos_url)}')
            if response.status_code == 200:
                print(f"影片發送到 Discord 頻道成功")
                firebase.set_latest_video_id(channel_handle=channel.id, latest_video_id=videos_id[0])
            else:
                print(f"影片發送到 Discord 頻道失敗")
        else:
            print(f"沒有新影片")

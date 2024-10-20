from dotenv import load_dotenv

import discord_bot
import youtube_crawler
from firebase import Firebase

load_dotenv()
firebase = Firebase()


def fetch_new_shorts(channel):
    latest_short = channel.get("latest_short")
    shorts_id = youtube_crawler.get_latest_shorts(
        channel_handle=channel.id, latest_short_id=latest_short.get("id"))
    filtered_shorts_id = []
    new_published_at = None
    for index, short_id in enumerate(shorts_id):
        if index == 0:
            published_at = youtube_crawler.get_video_published_at(video_id=short_id)
            if published_at > latest_short.get("published_at"):
                filtered_shorts_id.append(short_id)
                new_published_at = published_at
            else:
                break
        else:
            filtered_shorts_id.append(short_id)

    if filtered_shorts_id:
        shorts_url = [f"https://youtube.com/shorts/{id}" for id in filtered_shorts_id]
        response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                   content=f'{channel_name}上傳了短影片\n{"\n".join(shorts_url)}')
        if response.status_code == 200:
            print(f"短影片發送到 Discord 頻道成功")
            firebase.set_latest_short_info(channel_handle=channel.id, short_id=filtered_shorts_id[0],
                                           published_at=new_published_at)
        else:
            print(f"短影片發送到 Discord 頻道失敗")
    else:
        print(f"沒有新短影片")


def fetch_new_videos(channel):
    latest_video = channel.get("latest_video")
    videos_id = youtube_crawler.get_latest_videos(channel_handle=channel.id, latest_video_id=latest_video.get("id"))
    filtered_videos_id = []
    new_published_at = None
    for index, video_id in enumerate(videos_id):
        if index == 0:
            published_at = youtube_crawler.get_video_published_at(video_id=video_id)
            if published_at > latest_video.get("published_at"):
                filtered_videos_id.append(video_id)
                new_published_at = published_at
            else:
                break
        else:
            filtered_videos_id.append(video_id)
    if filtered_videos_id:
        videos_url = [f"https://youtu.be/{id}" for id in filtered_videos_id]
        response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                   content=f'{channel_name}上傳了影片\n{"\n".join(videos_url)}')
        if response.status_code == 200:
            print(f"影片發送到 Discord 頻道成功")
            firebase.set_latest_video_info(channel_handle=channel.id, video_id=filtered_videos_id[0],
                                           published_at=new_published_at)
        else:
            print(f"影片發送到 Discord 頻道失敗")
    else:
        print(f"沒有新影片")


def fetch_new_streams(channel):
    latest_stream = channel.get("latest_stream")
    streams_id = youtube_crawler.get_latest_streams(channel_handle=channel.id, latest_stream_id=latest_stream.get("id"))
    filtered_streams_id = []
    new_published_at = None
    for index, stream_id in enumerate(streams_id):
        if index == 0:
            published_at = youtube_crawler.get_video_published_at(video_id=stream_id)
            latest_stream_published_at = latest_stream.get("published_at")
            if latest_stream_published_at is None or published_at > latest_stream_published_at:
                filtered_streams_id.append(stream_id)
                new_published_at = published_at
            else:
                break
        else:
            filtered_streams_id.append(stream_id)
    if filtered_streams_id:
        streams_url = [f"https://www.youtube.com/live/{id}" for id in filtered_streams_id]
        response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                   content=f'{channel_name}正在直播\n{"\n".join(streams_url)}')
        if response.status_code == 200:
            print(f"直播發送到 Discord 頻道成功")
            firebase.set_latest_stream_info(channel_handle=channel.id, stream_id=filtered_streams_id[0],
                                            published_at=new_published_at)
        else:
            print(f"直播發送到 Discord 頻道失敗")
    else:
        print(f"沒有新直播")


for channel in firebase.get_channel_list():
    if channel.exists:
        channel_name = channel.get("channel_name")

        # 短影片
        print(f"{channel_name} 開始抓取新短影片...")
        fetch_new_shorts(channel)

        # 影片
        print(f"{channel_name} 開始抓取新影片...")
        fetch_new_videos(channel)

        # 直播
        print(f"{channel_name} 開始抓取新直播...")
        fetch_new_streams(channel)

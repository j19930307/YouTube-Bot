from dotenv import load_dotenv

import discord_bot
import youtube_crawler
from firebase import Firebase

load_dotenv()
firebase = Firebase()

for channel in firebase.get_channel_list():
    if channel.exists:
        channel_name = channel.get("channel_name")

        # 短影片
        print(f"{channel_name} 開始抓取新短影片...")
        latest_short = channel.get("latest_short")
        short_ids = youtube_crawler.get_latest_short_ids(channel_handle=channel.id,
                                                         latest_short_id=latest_short.get("id"))

        # 影片
        print(f"{channel_name} 開始抓取新影片...")
        latest_video = channel.get("latest_video")
        video_ids = youtube_crawler.get_latest_video_ids(channel_handle=channel.id,
                                                         latest_video_id=latest_video.get("id"))
        # 直播
        print(f"{channel_name} 開始抓取新直播...")
        latest_stream = channel.get("latest_stream")
        stream_ids = youtube_crawler.get_latest_stream_ids(channel_handle=channel.id,
                                                           latest_stream_id=latest_stream.get("id"))

        # 取得所有新影片 ID 後再一次查詢影片資訊以節省 API 請求配額
        all_video_ids = stream_ids + video_ids + short_ids

        if not all_video_ids:
            print(f"{channel_name} 沒有新影片")
            continue

        all_video_info = youtube_crawler.get_videos_info(video_ids=all_video_ids)

        shorts_info = [info for info in all_video_info if info.get("id") in short_ids]
        videos_info = [info for info in all_video_info if info.get("id") in video_ids]
        streams_info = [info for info in all_video_info if info.get("id") in stream_ids]

        # 短影片
        latest_short_published_at = latest_short.get("published_at")
        updated_shorts_info = [
            {**info, "published_at": youtube_crawler.get_video_published_at(info)}
            for info in shorts_info
        ]
        filtered_short_info = [
            info for info in updated_shorts_info
            if latest_short_published_at is None or info.get("published_at") > latest_short_published_at
        ]

        if filtered_short_info:
            videos_url = [f"https://youtu.be/{info.get("id")}" for info in filtered_short_info]
            response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                       content=f'{channel_name}上傳了短影片\n{"\n".join(videos_url)}')
            if response.status_code == 200:
                print(f"短影片發送到 Discord 頻道成功")
                firebase.set_latest_short_info(channel_handle=channel.id, short_id=filtered_short_info[0].get("id"),
                                               published_at=filtered_short_info[0].get("published_at"))
            else:
                print(f"短影片發送到 Discord 頻道失敗")
        else:
            print(f"沒有新短影片")

        # 影片
        latest_video_published_at = latest_video.get("published_at")
        updated_videos_info = [
            {**info, "published_at": youtube_crawler.get_video_published_at(info)}
            for info in videos_info
        ]
        filtered_video_info = [
            info for info in updated_videos_info
            if latest_video_published_at is None or info.get("published_at") > latest_video_published_at
        ]

        if filtered_video_info:
            videos_url = [f"https://youtu.be/{info.get('id')}" for info in filtered_video_info]
            response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                       content=f'{channel_name}上傳了影片\n{"\n".join(videos_url)}')
            if response.status_code == 200:
                print(f"影片發送到 Discord 頻道成功")
                firebase.set_latest_video_info(channel_handle=channel.id, video_id=filtered_video_info[0].get("id"),
                                               published_at=filtered_video_info[0].get("published_at"))
            else:
                print(f"影片發送到 Discord 頻道失敗")
        else:
            print(f"沒有新影片")

        # 直播
        latest_stream_published_at = latest_stream.get("published_at")
        updated_streams_info = [
            {**info, "published_at": youtube_crawler.get_video_published_at(info)}
            for info in streams_info
        ]
        filtered_stream_info = [
            info for info in updated_streams_info
            if latest_stream_published_at is None or info.get("published_at") > latest_stream_published_at
        ]

        if filtered_stream_info:
            videos_url = [f"https://youtu.be/{info.get('id')}" for info in filtered_stream_info]
            response = discord_bot.send_message_by_api(discord_channel_id=channel.get("discord_channel_id"),
                                                       content=f'{channel_name}上傳了直播\n{"\n".join(videos_url)}')
            if response.status_code == 200:
                print(f"直播發送到 Discord 頻道成功")
                firebase.set_latest_stream_info(channel_handle=channel.id, stream_id=filtered_stream_info[0].get("id"),
                                                published_at=filtered_stream_info[0].get("published_at"))
            else:
                print(f"直播發送到 Discord 頻道失敗")
        else:
            print(f"沒有新直播")

import json
import os
import re
from datetime import datetime, timezone

import googleapiclient.discovery
import requests
from lxml import html


def get_latest_video_ids(channel_handle: str, latest_video_id: str):
    videos_id = []
    text = requests.get(url=f'https://www.youtube.com/@{channel_handle}/videos').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是影片 (videos)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "videos":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']
            for content in contents:
                richItemRenderer = content.get('richItemRenderer', None)
                if richItemRenderer is not None:
                    videoRenderer = richItemRenderer['content']['videoRenderer']
                    video_id = videoRenderer['videoId']
                    if video_id == latest_video_id:
                        break
                    else:
                        videos_id.append(video_id)
    return videos_id


def get_latest_short_ids(channel_handle: str, latest_short_id: str):
    videos_id = []
    text = requests.get(url=f'https://www.youtube.com/@{channel_handle}/shorts').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是短影片 (shorts)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "shorts":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']
            for content in contents:
                richItemRenderer = content.get('richItemRenderer', None)
                if richItemRenderer is not None:
                    reelItemRenderer = richItemRenderer['content'].get('reelItemRenderer', None)
                    shortsLockupViewModel = richItemRenderer['content'].get('shortsLockupViewModel', None)
                    if reelItemRenderer is not None:
                        video_id = reelItemRenderer['videoId']
                        if video_id == latest_short_id:
                            break
                        else:
                            videos_id.append(video_id)
                    elif shortsLockupViewModel is not None:
                        video_id = shortsLockupViewModel['onTap']['innertubeCommand']['reelWatchEndpoint']['videoId']
                        if video_id == latest_short_id:
                            break
                        else:
                            videos_id.append(video_id)
    return videos_id


def get_latest_stream_ids(channel_handle: str, latest_stream_id: str):
    videos_id = []
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/streams').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是直播 (streams)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "streams":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']
            for content in contents:
                richItemRenderer = content.get('richItemRenderer', None)
                if richItemRenderer is not None:
                    videoRenderer = richItemRenderer['content']['videoRenderer']
                    if videoRenderer.get('upcomingEventData') is None:
                        video_id = videoRenderer['videoId']
                        if latest_stream_id and (video_id == latest_stream_id):
                            break
                        else:
                            videos_id.append(video_id)
    return videos_id


def get_videos_info(video_ids: list):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ["YOUTUBE_DATA_API_KEY"])
    request = youtube.videos().list(part="snippet", id=",".join(video_ids))
    response = request.execute()
    return response['items']


def get_video_published_at(item):
    snippet = item['snippet']
    live_broadcast_content = snippet['liveBroadcastContent']
    if live_broadcast_content == 'live':
        return datetime.now().replace(tzinfo=timezone.utc)
    elif live_broadcast_content == 'none':
        published_at = snippet['publishedAt']
        # 轉換成 datetime 對象
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

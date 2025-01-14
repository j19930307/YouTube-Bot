import json
import os
import re
from datetime import datetime, timezone

import googleapiclient.discovery
import requests
from lxml import html


def get_latest_videos(channel_handle: str, latest_video_id: str):
    text = requests.get(url=f'https://www.youtube.com/@{channel_handle}/videos').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    contents = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer']['content'][
        'richGridRenderer']['contents']

    videos_id = []

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


def get_latest_shorts(channel_handle: str, latest_short_id: str):
    text = requests.get(url=f'https://www.youtube.com/@{channel_handle}/shorts').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    contents = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs'][2]['tabRenderer']['content'][
        'richGridRenderer']['contents']

    videos_id = []

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


def get_latest_streams(channel_handle: str, latest_stream_id: str):
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/streams').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabRenderer = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs'][3].get('tabRenderer', None)
    if not tabRenderer:
        return []
    url = tabRenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
    match = re.search(r'/([^/]+)$', url)
    if match:
        if match.group(1) == "streams":
            contents = tabRenderer['content']['richGridRenderer']['contents']
            videos_id = []
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
    return []


def get_video_published_at(video_id: str):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ["YOUTUBE_DATA_API_KEY"])
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()

    if response['items']:
        snippet = response['items'][0]['snippet']
        live_broadcast_content = snippet['liveBroadcastContent']
        if live_broadcast_content == 'live':
            return datetime.now().replace(tzinfo=timezone.utc)
        elif live_broadcast_content == 'none':
            published_at = snippet['publishedAt']
            # 轉換成 datetime 對象
            return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    else:
        return None
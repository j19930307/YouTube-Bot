import json
import re

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
            videoRenderer = richItemRenderer['content']['reelItemRenderer']
            video_id = videoRenderer['videoId']
            if video_id == latest_short_id:
                break
            else:
                videos_id.append(video_id)
    return videos_id


def get_latest_streams(channel_handle: str, latest_streams_id: str):
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/streams').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabRenderer = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']
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
                    video_id = videoRenderer['videoId']
                    if latest_streams_id and (video_id == latest_streams_id):
                        break
                    else:
                        videos_id.append(video_id)
            return videos_id

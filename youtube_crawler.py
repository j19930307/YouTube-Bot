import json
import os
from datetime import datetime, timezone
from typing import Optional

import aiohttp
from lxml import html


class YouTubeCrawler:
    """YouTube 頻道爬蟲類，用於獲取頻道的影片、短影片和直播資訊"""

    def __init__(self, channel_handle: str, api_key: Optional[str] = None,
                 session: Optional[aiohttp.ClientSession] = None):
        self.channel_handle = channel_handle
        self.api_key = api_key or os.environ.get("YOUTUBE_DATA_API_KEY")
        self.session = session

    async def _fetch_text(self, url: str) -> str:
        async with self.session.get(url) as response:
            return await response.text()

    # ========= 抓影片 ID =========

    async def get_latest_video_ids(self, latest_video_id: str):
        videos_id = []
        try:
            text = await self._fetch_text(
                f'https://www.youtube.com/@{self.channel_handle}/videos'
            )

            tree = html.fromstring(text)
            ytVariableDeclaration = 'ytInitialData = '

            ytVariableData = None
            for script in tree.xpath('//script'):
                scriptContent = script.text_content()
                if ytVariableDeclaration in scriptContent:
                    ytVariableData = json.loads(
                        scriptContent.split(ytVariableDeclaration)[1][:-1]
                    )
                    break

            if not ytVariableData:
                return videos_id

            tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

            for tab in tabs:
                tabRenderer = tab.get('tabRenderer')
                if not tabRenderer:
                    continue

                url = tabRenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
                if url.endswith("videos"):
                    contents = tabRenderer['content']['richGridRenderer']['contents']
                    for content in contents:
                        richItemRenderer = content.get('richItemRenderer')
                        if not richItemRenderer:
                            continue

                        videoRenderer = richItemRenderer['content']['videoRenderer']
                        video_id = videoRenderer['videoId']

                        if video_id == latest_video_id:
                            break
                        videos_id.append(video_id)

            return videos_id

        except Exception as e:
            print(e)
            return videos_id

    async def get_latest_short_ids(self, latest_short_id: str):
        videos_id = []
        try:
            text = await self._fetch_text(
                f'https://www.youtube.com/@{self.channel_handle}/shorts'
            )

            tree = html.fromstring(text)
            ytVariableDeclaration = 'ytInitialData = '

            ytVariableData = None
            for script in tree.xpath('//script'):
                scriptContent = script.text_content()
                if ytVariableDeclaration in scriptContent:
                    ytVariableData = json.loads(
                        scriptContent.split(ytVariableDeclaration)[1][:-1]
                    )
                    break

            if not ytVariableData:
                return videos_id

            tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

            for tab in tabs:
                tabRenderer = tab.get('tabRenderer')
                if not tabRenderer:
                    continue

                url = tabRenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
                if url.endswith("shorts"):
                    contents = tabRenderer['content']['richGridRenderer']['contents']

                    for content in contents:
                        richItemRenderer = content.get('richItemRenderer')
                        if not richItemRenderer:
                            continue

                        reelItemRenderer = richItemRenderer['content'].get('reelItemRenderer')
                        shortsLockupViewModel = richItemRenderer['content'].get('shortsLockupViewModel')

                        if reelItemRenderer:
                            video_id = reelItemRenderer['videoId']
                        elif shortsLockupViewModel:
                            video_id = shortsLockupViewModel['onTap']['innertubeCommand']['reelWatchEndpoint'][
                                'videoId']
                        else:
                            continue

                        if video_id == latest_short_id:
                            break

                        videos_id.append(video_id)

            return videos_id

        except Exception as e:
            print(e)
            return videos_id

    async def get_latest_stream_ids(self, latest_stream_id: str):
        videos_id = []
        try:
            text = await self._fetch_text(
                f'https://www.youtube.com/@{self.channel_handle}/streams'
            )

            tree = html.fromstring(text)
            ytVariableDeclaration = 'ytInitialData = '

            ytVariableData = None
            for script in tree.xpath('//script'):
                scriptContent = script.text_content()
                if ytVariableDeclaration in scriptContent:
                    ytVariableData = json.loads(
                        scriptContent.split(ytVariableDeclaration)[1][:-1]
                    )
                    break

            if not ytVariableData:
                return videos_id

            tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

            for tab in tabs:
                tabRenderer = tab.get('tabRenderer')
                if not tabRenderer:
                    continue

                url = tabRenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
                if url.endswith("streams"):
                    contents = tabRenderer['content']['richGridRenderer']['contents']

                    for content in contents:
                        richItemRenderer = content.get('richItemRenderer')
                        if not richItemRenderer:
                            continue

                        videoRenderer = richItemRenderer['content']['videoRenderer']

                        if videoRenderer.get('upcomingEventData'):
                            continue

                        video_id = videoRenderer['videoId']

                        if latest_stream_id and video_id == latest_stream_id:
                            break

                        videos_id.append(video_id)

            return videos_id

        except Exception as e:
            print(e)
            return videos_id

    # ========= 影片詳細資訊 =========

    async def get_videos_info(self, video_ids: list):

        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet",
            "id": ",".join(video_ids),
            "key": self.api_key
        }

        async with self.session.get(url, params=params) as response:
            data = await response.json()
            return data.get("items", [])

    # ========= 發佈時間處理 =========

    def get_video_published_at(self, item):
        snippet = item['snippet']
        live_broadcast_content = snippet['liveBroadcastContent']

        if live_broadcast_content == 'live':
            return datetime.now(timezone.utc)

        published_at = snippet['publishedAt']
        return datetime.strptime(
            published_at,
            "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)

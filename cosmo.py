import asyncio
import io
import os
import sys
import tempfile
import time
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import aiohttp
import requests
from dotenv import load_dotenv

import sns_core.clients.discord_messages as dm
from sns_core import build_embeds, build_text_embed
from sns_core.models import SocialPost, PostAuthor
from sns_core.clients.discord_messages import post_message

from firebase import Firebase

# 註冊 Cosmo Room 來源圖示與名稱
dm._SOURCE_MAP["shop.cosmo.fans"] = ("Cosmo Room", "https://static.cosmo.fans/assets/triples-logo.png")
dm._SOURCE_MAP["cosmo.fans"] = ("Cosmo Room", "https://static.cosmo.fans/assets/triples-logo.png")


def sync_posts_to_supabase(posts: list[dict], artist_id: str = "tripleS"):
    """將 Cosmo 貼文全量同步至 Supabase，包含 videoItem.channels、accessType 與 duration"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return

    url = f"{supabase_url}/rest/v1/room_posts"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal"
    }

    batch = []
    for post in posts:
        video_item = post.get("videoItem") or {}
        channels = video_item.get("channels", [])
        access_type = video_item.get("accessType", "")
        duration = video_item.get("duration", 0)

        batch.append({
            "id": post.get("id"),
            "artist_id": artist_id,
            "kind": post.get("kind", "post"),
            "author_name": post.get("author", {}).get("nickname", "Artist"),
            "author_avatar": post.get("author", {}).get("profileImage", ""),
            "content": post.get("content", ""),
            "media": post.get("media", []),
            "channels": channels,
            "access_type": access_type,
            "duration": duration,
            "media_aspect_ratio": post.get("mediaAspectRatio", ""),
            "created_at": post.get("createdAt")
        })

    try:
        resp = requests.post(url, headers=headers, json=batch, timeout=15)
        if resp.status_code in (200, 201, 204):
            print(f"⚡ 成功同步 {len(batch)} 篇貼文至 Supabase (包含 duration 秒數)")
        else:
            print(f"⚠️ Supabase 同步失敗 Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"⚠️ 寫入 Supabase 時發生例外: {e}")


async def process_cosmo_room_posts(firebase: Firebase, session: aiohttp.ClientSession):
    user_session = os.environ.get("COSMO_USER_SESSION")
    discord_channel_id = os.environ.get("COSMO_ROOM_DISCORD_CHANNEL_ID")
    artist_id = "tripleS"

    if not discord_channel_id:
        print("⚠️ 未設定 COSMO_ROOM_DISCORD_CHANNEL_ID，跳過 Cosmo Room Posts 檢查")
        return

    if not user_session:
        print("⚠️ 未設定 COSMO_USER_SESSION，跳過 Cosmo Room Posts 檢查")
        return

    url = f"https://shop.cosmo.fans/bff/v4/room-posts?artistId={artist_id}&take=10&skip=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Cookie": f"user-session={user_session}"
    }

    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ 取得 Cosmo Room Posts 失敗 (Status {resp.status})")
                return
            data = await resp.json()
    except Exception as e:
        print(f"❌ 請求 Cosmo Room Posts 時發生錯誤: {e}")
        return

    posts = data.get("posts", [])
    if not posts:
        print(f"Cosmo Room Posts 沒有資料")
        return

    # 1. 將本輪取得的所有 Room Posts 同步至 Supabase
    sync_posts_to_supabase(posts, artist_id=artist_id)

    # 2. 檢查是否有需要發送 Discord 通知的「一般貼文 (kind == post)」
    latest_info = firebase.get_latest_cosmo_room_post_info(artist_id=artist_id)
    latest_saved_id = latest_info.get("id", 0)

    new_posts = [p for p in posts if p.get("id") > latest_saved_id and p.get("kind") == "post"]

    if not new_posts:
        print(f"Cosmo Room Posts ({artist_id}) 沒有新貼文通知")
        return

    new_posts.sort(key=lambda x: x.get("id"))
    print(f"🎉 偵測到 {len(new_posts)} 篇 Cosmo Room 新貼文！準備使用 sns_core 發送至 Discord...")

    for post in new_posts:
        post_id = post.get("id")
        author_info = post.get("author", {})
        author_name = author_info.get("nickname", "Artist")
        profile_img = author_info.get("profileImage", "")
        content = post.get("content", "")
        created_at_str = post.get("createdAt")
        media_list = post.get("media", [])

        dt = None
        if created_at_str:
            try:
                dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

        author_obj = PostAuthor(name=author_name, url=profile_img)
        images = [m.get("url") for m in media_list if m.get("kind") == "image" and m.get("url")]
        videos = [m.get("url") for m in media_list if m.get("kind") == "video" and m.get("url")]

        social_post = SocialPost(
            post_link=f"https://shop.cosmo.fans/bff/v4/room-posts/{post_id}",
            author=author_obj,
            text=content,
            images=images,
            videos=videos,
            created_at=dt
        )

        use_build_embeds = (len(images) <= 4 and len(videos) == 0)

        try:
            if use_build_embeds:
                embeds = build_embeds(social_post)
                post_message(
                    channel_id=discord_channel_id,
                    embeds=embeds,
                    show_all=False
                )
            else:
                embeds = build_text_embed(social_post)

                # 1. 先發送文字 Embed 卡片
                post_message(
                    channel_id=discord_channel_id,
                    embeds=embeds,
                    show_all=False
                )

                # 2. 下載所有實體媒體檔案並接在 Embed 後面發送
                temp_dir = tempfile.mkdtemp()
                downloaded_files = []
                oversized_media_urls = []
                all_media_urls = images + videos

                for m_idx, media_url in enumerate(all_media_urls):
                    try:
                        async with session.get(media_url) as media_resp:
                            if media_resp.status == 200:
                                file_data = await media_resp.read()
                                filename = media_url.split("/")[-1].split("?")[0]
                                if not filename:
                                    filename = f"media_{m_idx + 1}.jpg"

                                if len(file_data) > 25 * 1024 * 1024:
                                    print(f"⚠️ 媒體檔案容量 ({len(file_data) / (1024*1024):.2f}MB) 超過 Discord 25MB 限制，改用 URL 連結發送")
                                    oversized_media_urls.append(media_url)
                                else:
                                    temp_file_path = os.path.join(temp_dir, filename)
                                    with open(temp_file_path, "wb") as f:
                                        f.write(file_data)
                                    downloaded_files.append(temp_file_path)
                    except Exception as e:
                        print(f"下載 Cosmo 媒體檔案失敗 {media_url}: {e}")

                try:
                    if downloaded_files:
                        chunk_size = 10
                        for i in range(0, len(downloaded_files), chunk_size):
                            chunk_files = downloaded_files[i:i + chunk_size]
                            post_message(
                                channel_id=discord_channel_id,
                                file_paths=chunk_files,
                                show_all=False
                            )
                            await asyncio.sleep(1.0)

                    if oversized_media_urls:
                        links_text = "\n".join([f"{url}" for url in oversized_media_urls])
                        post_message(
                            channel_id=discord_channel_id,
                            content=links_text,
                            show_all=False
                        )
                finally:
                    for fp in downloaded_files:
                        try:
                            os.remove(fp)
                        except Exception:
                            pass
                    try:
                        os.rmdir(temp_dir)
                    except Exception:
                        pass

            print(f"✅ Cosmo Room 貼文 #{post_id} ({author_name}) 成功發送到 Discord 頻道 (use_build_embeds={use_build_embeds})")
            firebase.set_latest_cosmo_room_post_info(
                artist_id=artist_id,
                post_id=post_id,
                published_at=created_at_str,
                author=author_name,
                content=content
            )

        except Exception as e:
            print(f"❌ Cosmo Room 貼文 #{post_id} 發送至 Discord 失敗: {e}")

        await asyncio.sleep(1.0)


async def main():
    load_dotenv()

    firebase = Firebase()

    start_time = time.perf_counter()
    print("🚀 [Cosmo Room Posts] 開始執行貼文檢查...")

    async with aiohttp.ClientSession() as session:
        await process_cosmo_room_posts(firebase, session)

    end_time = time.perf_counter()
    print(f"✅ [Cosmo Room Posts] 檢查完成，總耗時: {end_time - start_time:.2f} 秒")


if __name__ == "__main__":
    asyncio.run(main())

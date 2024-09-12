import base64
import json
import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


def base64_decode(key) -> dict:
    decoded_bytes = base64.b64decode(key)
    decoded_string = decoded_bytes.decode('utf-8')
    return json.loads(decoded_string)


class Firebase:
    def __init__(self):
        certificate = credentials.Certificate(base64_decode(os.environ["FIREBASE_ADMIN_KEY"]))
        firebase_admin.initialize_app(certificate)
        self.__db = firestore.client()

    def get_channel_list(self):
        return self.__db.collection("YouTube").stream()

    def set_latest_short_info(self, channel_handle: str, short_id: str, published_at: datetime):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_short": {
                "id": short_id,
                "published_at": published_at
            }
        })

    def set_latest_video_info(self, channel_handle: str, video_id: str, published_at: datetime):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_video": {
                "id": video_id,
                "published_at": published_at
            }
        })

    def set_latest_stream_info(self, channel_handle: str, stream_id: str, published_at: datetime):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_stream": {
                "id": stream_id,
                "published_at": published_at
            }
        })

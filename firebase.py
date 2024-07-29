import base64
import json
import os

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

    def set_latest_short_id(self, channel_handle: str, latest_short_id: str):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_short_id": latest_short_id
        })

    def set_latest_video_id(self, channel_handle: str, latest_video_id: str):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_video_id": latest_video_id
        })

    def set_latest_stream_id(self, channel_handle: str, latest_stream_id: str):
        doc_ref = self.__db.collection("YouTube").document(channel_handle)
        doc_ref.update({
            "latest_stream_id": latest_stream_id
        })

"""
Short drama playback support for iQIYI API v2.0.0

Implementation plan based on Burp captures and Frida analysis.
"""

# Expected request/response flow:

# 1. GET /video/play?s2=short_ply (metadata + subtitle_list)
#    Sign header: MD5(sorted_query_params)
#    Response: 
#    {
#      "code": 0,
#      "success": true,
#      "video": {
#        "_pid": "2735084731741600",
#        "duration": 3600,
#        "play_mode": 2,
#        "subtitle_list": [
#          {"language_type": 1, "make_version": "101"},
#          {"language_type": 2, "make_version": "101"}
#        ]
#      },
#      "album": {"_pid": "8119221898348201"}
#    }

# 2. GET /cache-video.iq.com/dash or similar (actual streams)
#    Parameters: tvid, bid, tm, auth, vf (signature)
#    Response: {program: {video: [], stl: [], audio: []}}

# Key differences from standard drama:
# - s2=short_ply marker in /video/play
# - play_mode: 2 in response
# - May have subtitle_list with language_type instead of lid
# - Might need separate /dash call for streams

# Subtitle language_type mapping (from response):
LANGUAGE_TYPE_MAP = {
    1: ("English", "en"),
    2: ("Mandarin Chinese", "zh-CN"),
    3: ("Cantonese", "zh-HK"),
    4: ("Japanese", "ja"),
    5: ("Korean", "ko"),
    6: ("Spanish", "es"),
    18: ("Indonesian", "id"),
    21: ("Thai", "th"),
    23: ("Vietnamese", "vi"),
    24: ("Malay", "ms"),
    26: ("Traditional Chinese", "zh-TW"),
    27: ("Turkish", "tr"),
    28: ("Russian", "ru"),
    30: ("Portuguese", "pt"),
}

# Implementation checklist:
# [ ] Extract signing algorithm from Frida capture
# [ ] Implement generate_video_play_sign() in Signer
# [ ] Implement get_playback_short_drama() in IQIYIClient
# [ ] Map language_type to language codes
# [ ] Parse subtitle_list response
# [ ] Handle stream endpoint (may need /dash or direct from /video/play)
# [ ] Add route dispatcher in routes_playback.py
# [ ] Add tests for short drama parsing
# [ ] Update CHANGELOG.md with short drama support

print("Waiting for Frida capture data...")
print("Expected: /video/play request with Sign header and response with subtitle_list")

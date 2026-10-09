import dataclasses
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Stream:
    format: str
    id: str
    url: str
    resolutions: str
    size: str
    duration: int
    codec_name: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stream':
        return cls(
            format=data.get("format", ""),
            id=data.get("id", ""),
            url=data.get("url", ""),
            resolutions=data.get("resolutions", ""),
            size=data.get("size", "0"),
            duration=data.get("duration", 0),
            codec_name=data.get("codecName", "")
        )

@dataclass
class Caption:
    id: str
    lan: str
    lan_name: str
    url: str
    size: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Caption':
        return cls(
            id=data.get("id", ""),
            lan=data.get("lan", ""),
            lan_name=data.get("lanName", ""),
            url=data.get("url", ""),
            size=data.get("size", "0")
        )

@dataclass
class Dub:
    subject_id: str
    lan_name: str
    lan_code: str
    is_original: bool
    type: int
    detail_path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dub':
        return cls(
            subject_id=str(data.get("subjectId", data.get("subject_id", ""))),
            lan_name=data.get("lanName", data.get("lan_name", "")),
            lan_code=data.get("lanCode", data.get("lan_code", "")),
            is_original=data.get("original", data.get("is_original", False)),
            type=data.get("type", 0),
            detail_path=data.get("detailPath", data.get("detail_path", ""))
        )

@dataclass
class PlayData:
    streams: List[Stream]
    free_num: int
    limited: bool
    has_resource: bool
    captions: List[Caption] = dataclasses.field(default_factory=list)
    dubs: List[Dub] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayData':
        return cls(
            streams=[Stream.from_dict(s) for s in data.get("streams", [])],
            free_num=data.get("freeNum", data.get("free_num", 0)),
            limited=data.get("limited", False),
            has_resource=data.get("hasResource", data.get("has_resource", False)),
            captions=[Caption.from_dict(c) for c in data.get("captions", [])],
            dubs=[Dub.from_dict(d) for d in data.get("dubs", [])]
        )

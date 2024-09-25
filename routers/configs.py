from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SocialMediaRecommendation(BaseModel):
    platform: str
    max_hashtags_char: str
    recommendation: str


class ConfigResponse(BaseModel):
    enable_billing: bool
    enable_ads: bool
    max_request: str
    social_media_recomendation: List[SocialMediaRecommendation]



@router.get("/configs")
async def getConfigs():
    recommendations = [
        SocialMediaRecommendation(platform="Instagram", max_hashtags_char="30 HashTags", recommendation="Use all 30 hashtags, as they can be hidden under the caption."),
        SocialMediaRecommendation(platform="TikTok", max_hashtags_char="120 Characters", recommendation="Use 5-8 most relevant hashtags in your video caption."),
        SocialMediaRecommendation(platform="X (Twitter)", max_hashtags_char="280 Characters", recommendation="Use 3-5 most relevant hashtags per tweet."),
        SocialMediaRecommendation(platform="YouTube", max_hashtags_char="15 HashTags", recommendation="Use 3 most relevant hashtags in the title to avoid being removed from search."),
        SocialMediaRecommendation(platform="LinkedIn", max_hashtags_char="Unlimited", recommendation="Use 5-8 most relevant hashtags; avoid over-tagging for better appearance."),
        SocialMediaRecommendation(platform="Snapchat", max_hashtags_char="Unlimited", recommendation="Use 2-3 most relevant hashtags in Spotlight."),
        SocialMediaRecommendation(platform="Pinterest", max_hashtags_char="20 HashTags", recommendation="Use 5-8 most relevant hashtags on your pins."),
        SocialMediaRecommendation(platform="Facebook", max_hashtags_char="Unlimited", recommendation="Use 2-5 relevant hashtags; too many can reduce engagement."),
        SocialMediaRecommendation(platform="Threads", max_hashtags_char="10 HashTags", recommendation="Use 3-5 relevant hashtags to improve visibility and engagement."),
    ]


    return {
        "status":True,
        "message":"App config fetched success",
        "data":ConfigResponse(
                enable_billing=False,
                enable_ads=False,
                max_request="unlimited",
                social_media_recomendation = recommendations
            )
    }
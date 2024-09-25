from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
import re
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from g4f.client import Client 
import json 

router = APIRouter()

# Define the response model for hashtags
class HashtagResponse(BaseModel):
    name: str
    tags: List[str]

# Define the request model for prompts
class PromptRequest(BaseModel):
    prompt: str
    max_token: int

def format_text(text: str) -> str:
    return text.strip()  # Clean up the text by stripping whitespace

def generate_hashtags_sync(prompt: str, maxToken: int, isHashTagRequest: bool) -> Tuple[List[HashtagResponse], str, Dict[str, Any]]:
    try:
        client = Client()  # Ensure this client is synchronous

        start_time = datetime.now()
        print(f"Request sent at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        provider = "Nexra" if isHashTagRequest else None # "Nexra",

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            provider = provider,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=maxToken
        )   
        
        print("Provider Type :", response.provider)
        generated_text = response.choices[0].message.content.strip()
        
        print("Generated Text:", generated_text)
        
        hashData = None
        if isHashTagRequest:
            try:
                # Try to parse as JSON
                json_data = json.loads(generated_text)  # Parse directly
                if "data" in json_data:
                    hashData = json_data["data"]
                else:
                    raise ValueError("Parsed JSON does not contain 'data' key.")
            except json.JSONDecodeError:
                # If the response is not valid JSON, log and raise an error
                print("Received non-JSON response. Attempting to parse differently...")
                if generated_text.startswith("_") or generated_text.startswith("__"):  # Check if it's the second format
                    generated_text = generated_text.lstrip("_")  # Remove leading underscores
                json_data = json.loads(generated_text)  
                #print("non-JSON response", json_data["gpt"])
                json_data = json.loads(json_data["gpt"])  
                if "data" in json_data:
                    hashData = json_data["data"]
                else:
                    raise ValueError("Parsed JSON does not contain 'data' key.")
        



        timing_info = {
            "request_time": start_time.isoformat(),
            "response_time": datetime.now().isoformat(),
            "total_duration_seconds": (datetime.now() - start_time).total_seconds()
        }

        formatted_text = {
            "model": response.model,
            "provider": response.provider,
            "message": response.choices[0].message.content
        }


        return hashData, formatted_text, timing_info

    except Exception as e:
        print(f"An error occurred: {e}")
        return [], None, {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "context": "Error in hashtag generation"
        }




# Limit thread pool size
# THREAD_POOL_SIZE = 2000
# async def run_sync_task(prompt: str, maxToken: int, isHashTagRequest: bool) -> Tuple[List[HashtagResponse], str, Dict[str, Any]]:
#     loop = asyncio.get_event_loop()
#     with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as pool:
#         result = await loop.run_in_executor(pool, generate_hashtags_sync, prompt, maxToken, isHashTagRequest)
#     return result

async def run_sync_task(prompt: str, maxToken: int , isHashTagRequest: bool) -> Tuple[List[HashtagResponse], str, Dict[str, Any]]:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, generate_hashtags_sync, prompt, maxToken , isHashTagRequest)
    return result



@router.post("/generate-hashtags")
async def generate_hashtags_endpoint(request: PromptRequest):
    try:
        hashtags, _, timing_info = await run_sync_task(request.prompt, request.max_token , True)
        if hashtags:
            return {
                "status": True,
                "message": "Hashtags have been generated",
                "data": hashtags,
                "timing_info": timing_info
            }
        else:
            raise HTTPException(status_code=500, detail="No hashtags generated")
    except Exception as e:
        return {
            "status": False,
            "message": "Hashtags not generated due to some error",
            "data": str(e),
            "timing_info": {"error": str(e)}
        }

@router.post("/generate-full-response")
async def generate_full_response_endpoint(request: PromptRequest):
    try:
        _, full_response, timing_info = await run_sync_task(request.prompt, request.max_token , False)
        if full_response:
            return {
                "status": True,
                "message": "Full response has been generated",
                "data": full_response,
                "timing_info": timing_info
            }
        else:
            raise HTTPException(status_code=500, detail="No response generated")
    except Exception as e:
        return {
            "status": False,
            "message": "Full response not generated due to some error",
            "data": str(e),
            "timing_info": {"error": str(e)}
        }
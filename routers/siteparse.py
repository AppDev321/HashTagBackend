from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Union
import httpx
from bs4 import BeautifulSoup
import asyncio
import datetime
import json
import os
from sqlalchemy.orm import Session
from models.hashtag_database_model import SessionLocal, SearchTag




# File paths
cache_file = "/tmp/hashtags_cache.json"


router = APIRouter()



# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class HashtagData(BaseModel):
    id: int
    tag: str
    usage: Union[int, float]   

class SearchTagResponse(BaseModel):
    best: List[HashtagData]
    top: List[HashtagData]
    recommended: List[HashtagData]
    exact: List[HashtagData]
    popular: List[HashtagData]
    related: List[HashtagData]

semaphore = asyncio.Semaphore(500)  # Limit to 10 concurrent requests
request_time_out = 180.0

async def get_new_hash_tags() -> List[HashtagData]:
    base_url = "https://best-hashtags.com/new-hashtags.php?pageNum_tag={}&totalRows_tag=1000"
    data_list = []

    async with httpx.AsyncClient() as client:
        for page_num in range(10):  # Fetch multiple pages
            url = base_url.format(page_num)
            async with semaphore:  # Limit concurrency
                response = await client.get(url, timeout=request_time_out)  # Set timeout
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', class_='table table-striped')

                for row in table.find_all('tr')[1:]:  # Skip header row
                    columns = row.find_all('td')

                    if len(columns) >= 3:
                        id_value = int(columns[0].text.strip())
                        tag_value = columns[1].text.strip()
                        usage_value = int(columns[2].text.strip().replace(',', ''))

                        data_list.append(HashtagData(
                            id=id_value,
                            tag=tag_value,
                            usage=usage_value
                        ))

    return data_list

async def get_best_hash_tags() -> List[HashtagData]:
    base_url = "https://best-hashtags.com/best-hashtags.php"
    data_list = []

    async with httpx.AsyncClient() as client:
        async with semaphore:  # Limit concurrency
            response = await client.get(base_url, timeout=request_time_out)  # Set timeout
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='table table-striped')

            for row in table.find_all('tr')[1:]:  # Skip header row
                columns = row.find_all('td')

                if len(columns) >= 3:
                    id_value = int(columns[0].text.strip())
                    tag_value = columns[1].text.strip()
                    usage_value = int(columns[2].text.strip().replace(',', ''))

                    data_list.append(HashtagData(
                        id=id_value,
                        tag=tag_value,
                        usage=usage_value
                    ))

    return data_list

async def get_search_hash_tags(searchValue: str, db: Session) -> SearchTagResponse:
    base_url = f"https://best-hashtags.com/hashtag/{searchValue}"
    recommended_tags = []
    best_tags = []
    top_tags = []
    exact_tags = []
    popular_tags = []
    related_tags = []


    # Check if any tags already exist in the database
    existing_tags = db.query(SearchTag).filter(SearchTag.searchWord == searchValue).first()

    if existing_tags: 
        # return same list of tags in response class
        print("Fetch search record from database")
        return SearchTagResponse(
            best=[HashtagData(**tag) for tag in existing_tags.best],
            top=[HashtagData(**tag) for tag in existing_tags.top],
            recommended=[HashtagData(**tag) for tag in existing_tags.recommended],
            exact=[HashtagData(**tag) for tag in existing_tags.exact],
            popular=[HashtagData(**tag) for tag in existing_tags.popular],
            related=[HashtagData(**tag) for tag in existing_tags.related],
        )
    
    
    
    print("Fetch search record from website")
    async with httpx.AsyncClient() as client:
        try:
            async with semaphore:  # Limit concurrency
                response = await client.get(base_url, timeout=request_time_out)  # Set timeout
                response.raise_for_status()  # Raise an error for bad responses
                soup = BeautifulSoup(response.content, 'html.parser')

                # Recommended hashtags
                recommended_section = soup.find('h3', text='Recommended HashTags')
                if recommended_section:
                    ul = recommended_section.find_next('ul')
                    if ul:
                        for li in ul.find_all('li'):
                            a_tag = li.find('a')
                            if a_tag:
                                tag_value = a_tag.text.strip()
                                recommended_tags.append(HashtagData(
                                    id=len(recommended_tags) + 1,
                                    tag=tag_value,
                                    usage=100
                                ))

                # Top hashtags
                div_top = soup.find('div', class_='progression')
                if div_top:
                    for h3 in soup.find_all('h3', class_='heading-xs list-unstyled save-job'):
                        a_tag = h3.find('a')
                        if a_tag:
                            aria_value = h3.find_next('div', class_='progress').find('div', class_='progress-bar')['aria-valuenow']
                            top_tags.append(HashtagData(
                                id=len(top_tags) + 1,
                                tag=a_tag.text.strip(),
                                usage=float(aria_value)
                            ))


                # Best hashtags
                tag_box = soup.find('div', class_='tag-box tag-box-v3 margin-bottom-40')
                if tag_box:
                    p1_tag = tag_box.find('p1')  
                    if p1_tag:
                        hashtags = p1_tag.text.strip().split()
                        for hashtag in hashtags:
                            best_tags.append(HashtagData(
                                id=len(best_tags) + 1,
                                tag=hashtag,
                                usage=100  # You can replace this with actual usage if needed
                            ))
                           

                # Exact hashtags
                div_exact = soup.find('div', id='exact')
                if div_exact:
                    rows = div_exact.find_all('tr')
                    for row in rows:
                        columns = row.find_all('td')
                        if len(columns) >= 3:
                            id_value = int(columns[0].text.strip())
                            tag_value = columns[1].text.strip()
                            usage_value = int(columns[2].text.strip().replace(',', ''))
                            exact_tags.append(HashtagData(id=id_value, tag=tag_value, usage=usage_value))

                # Popular hashtags
                div_popular = soup.find('div', id='popular')
                if div_popular:
                    rows = div_popular.find_all('tr')
                    for row in rows:
                        columns = row.find_all('td')
                        if len(columns) >= 3:
                            id_value = int(columns[0].text.strip())
                            tag_value = columns[1].text.strip()
                            usage_value = int(columns[2].text.strip().replace(',', ''))
                            popular_tags.append(HashtagData(id=id_value, tag=tag_value, usage=usage_value))

                # Related hashtags
                div_related = soup.find('div', id='related')
                if div_related:
                    rows = div_related.find_all('tr')
                    for row in rows:
                        columns = row.find_all('td')
                        if len(columns) >= 3:
                            id_value = int(columns[0].text.strip())
                            tag_value = columns[1].text.strip()
                            usage_value = int(columns[2].text.strip().replace(',', ''))
                            related_tags.append(HashtagData(id=id_value, tag=tag_value, usage=usage_value))

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Store same list of tags in database 
    store_search_hashtags(searchValue, best_tags, top_tags, recommended_tags, exact_tags, popular_tags, related_tags)

    return SearchTagResponse(
        best=best_tags,
        exact=exact_tags,
        popular=popular_tags,
        related=related_tags,
        top=top_tags,
        recommended=recommended_tags
    )

def store_search_hashtags(search_word, best_tags, top_tags, recommended_tags, exact_tags, popular_tags, related_tags):
    db = SessionLocal()
    try:
        new_entry = SearchTag(
            searchWord=search_word,
            best=[tag.dict() for tag in best_tags],         
            top=[tag.dict() for tag in top_tags],
            recommended=[tag.dict() for tag in recommended_tags],
            exact=[tag.dict() for tag in exact_tags],
            popular=[tag.dict() for tag in popular_tags],
            related=[tag.dict() for tag in related_tags]
        )
        db.add(new_entry)
        db.commit()
    finally:
        db.close()


@router.get("/getNewTags", response_model=dict)
async def get_new_tags():
    cache = read_cache()
    last_update = datetime.datetime.fromisoformat(cache["last_update"]) if cache["last_update"] else datetime.datetime.min

    if (datetime.datetime.now() - last_update).days >= 1:
        await update_cache()
        cache = read_cache()  # Refresh cache from file after update
        print("Data loaded from site and cached.")
    else:
        print("Data loaded from cache.")

    return {
        "status": True,
        "message": "Data fetched successfully",
        "data": [HashtagData(**tag) for tag in cache["new_tags"]]
    }



@router.get("/getBestTags", response_model=dict)
async def get_best_tags():
    cache = read_cache()
    last_update = datetime.datetime.fromisoformat(cache["last_update"]) if cache["last_update"] else datetime.datetime.min


    if (datetime.datetime.now() - last_update).days >= 1:
        await update_cache()
        cache = read_cache()  # Refresh cache from file after update
        print("Data loaded from site and cached.")
    else:
        print("Data loaded from cache.")

    return {
        "status": True,
        "message": "Data fetched successfully",
        "data": [HashtagData(**tag) for tag in cache["best_tags"]]
    }

@router.get("/getSearchTags/{value}", response_model=dict)
async def get_search_tags(value: str, db: Session = Depends(get_db)):
    data = await get_search_hash_tags(searchValue=value, db=db)  # Pass the db session here
    if not (data.best or data.top or data.recommended or data.exact or data.popular or data.related):
        return {
            "status": False,
            "message": "Data Not found",
            "data": None
        }
    
    return {
        "status": True,
        "message": "Data fetched successfully",
        "data": data
    }




 # Caching data mechanizm to reduce network call to website for data parsing

def read_cache() -> dict:
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {"new_tags": [], "best_tags": [], "last_update": ""}

def write_cache(new_tags: List[HashtagData], best_tags: List[HashtagData]):
    with open(cache_file, "w") as f:
        json.dump({
            "new_tags": [tag.dict() for tag in new_tags],
            "best_tags": [tag.dict() for tag in best_tags],
            "last_update": datetime.datetime.now().isoformat()
        }, f)

async def update_cache():
    new_tags = await get_new_hash_tags()
    best_tags = await get_best_hash_tags()
    write_cache(new_tags, best_tags)
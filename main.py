import asyncio
from enum import Enum
from pathlib import Path

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel
from slugify import slugify

from configs import get_configs


class ImageData(BaseModel):
    url: str
    filename: str


class TagName(Enum):
    DIV = 'div'
    A = 'a'
    UL = 'ul'
    HREF = 'href'
    SECTION = 'section'
    H1 = 'h1'


BASE_URL = get_configs().base_url
SAVE_DIR = get_configs().save_dir


async def main(url: str = BASE_URL, save_dir: str = SAVE_DIR) -> None:
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    base_page_text = await page_request(url=url)
    engine_urls = await parse(text=base_page_text)
    images_data = [parse_one_page(url=eng_url) for eng_url in engine_urls]
    results = await asyncio.gather(*images_data)
    tasks = [save_image(**img_data.dict(), save_dir=save_dir) for img_data in results]
    await asyncio.gather(*tasks)


async def page_request(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            if response.status != 200:
                print('something wrong!!!')
            return await response.text()


def get_soup(text: str, parser: str = 'lxml') -> BeautifulSoup:
    return BeautifulSoup(text, parser)


async def parse(text: str) -> list[str]:
    soup = get_soup(text=text)
    root = soup \
        .find(TagName.DIV.value, class_='site-root') \
        .find(TagName.DIV.value, class_='comp-jh51issm')
    container = root.find(TagName.UL.value, class_='S4WbK_ uQ5Uah c2Zj9x')
    engines = container.find_all(TagName.DIV.value, class_='ETPbIy')
    return [eng.find(TagName.A.value, class_='oQUvqL x5qIv3')[TagName.HREF.value] for eng in engines]


async def parse_one_page(url: str) -> ImageData:
    text = await page_request(url=url)
    soup = get_soup(text=text)
    sections = soup.find_all(TagName.SECTION.value, class_='EeCU_')
    engine_name = sections[-1].find(TagName.H1.value, class_='_2qrJF igTU-').text.strip()
    image_url = sections[0].find(TagName.DIV.value, class_='_3j9OG media-wrapper-hook V-iTp')[TagName.HREF.value]
    return ImageData(url=image_url, filename=engine_name)


async def save_image(url: str, filename: str, save_dir: str) -> None:
    filename = f'{save_dir}/{slugify(text=filename)}.jpg'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            async with aiofiles.open(file=filename, mode='wb') as file:
                await file.write(await response.read())


if __name__ == '__main__':
    asyncio.run(main())

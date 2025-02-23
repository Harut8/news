from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from src.app.crawler.service import ParsingService, CrawlerService
from src.core.di import DependencyContainer
from src.core.utils.api.cbv import cbv
from src.core.utils.api.response import ResponseDto
from src.core.utils.base_value_objects import UrlString

crawler_router = APIRouter(
    responses={404: {"description": "Not found"}},
)

@cbv(crawler_router)
class CrawlerController:

    @crawler_router.get("/health")
    @inject
    async def health(self)-> ResponseDto[str]:
        return ResponseDto(data="healthy")

    @crawler_router.post("/schedule-urls")
    @inject
    async def add_url(self,
                      urls: list[UrlString],
                      crawler_service: CrawlerService = Depends(Provide[DependencyContainer.crawling_service]))->ResponseDto[list]:
        await crawler_service.schedule_urls(urls)
        return ResponseDto(data=urls)

    @crawler_router.get("/sub-urls")
    @inject
    async def find_sub_urls(self,
                            url: UrlString,
                            crawler_service: CrawlerService = Depends(Provide[DependencyContainer.crawling_service]))->ResponseDto[list]:
        _sub_urls = await crawler_service.find_sub_urls(url)
        return ResponseDto(data=_sub_urls)

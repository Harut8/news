from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.app.crawler.service import CrawlerService
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
    async def health(self) -> ResponseDto[str]:
        return ResponseDto(data="healthy")

    @crawler_router.post("/schedule-urls")
    @inject
    async def add_url(
        self, urls: list[UrlString], crawler_service: CrawlerService = Depends(Provide[DependencyContainer.crawling_service])
    ) -> ResponseDto[list]:
        await crawler_service.schedule_urls(urls)
        return ResponseDto(data=urls)

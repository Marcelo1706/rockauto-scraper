import scrapy
from scrapy.settings import BaseSettings


class OemSpider(scrapy.Spider):
    name = "oem_spider"
    allowed_domains = ["rockauto.com"]
    max_retries = 5

    def __init__(self, oem_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oem_list = oem_list
        self.retries = {}

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        settings.set("FEED_EXPORT_ENCODING", "utf-8")
        settings.set("RETRY_TIMES", 5)
        settings.set("RETRY_HTTP_CODES", [302, 404, 502])

    def start_requests(self):
        for oem in self.oem_list:
            url = f"https://www.rockauto.com/es/partsearch/?partnum={oem}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "oem": oem,
                    "proxy": "http://brd-customer-hl_2fc871a8-zone-datacenter_proxy1:r3miq3roxhg9@brd.superproxy.io:33335",
                    "handle_httpstatus_list": [302, 404, 502],
                },
            )

    def parse(self, response):
        if response.status in (302, 404, 502):
            retries = self.retries.setdefault(response.url, 0)
            if retries < self.max_retries:
                self.retries[response.url] += 1
                yield response.request.replace(dont_filter=True)
            else:
                self.logger.error(
                    "%s still returns 302 responses after %s retries", response.url, retries
                )
                yield {
                    "oem": response.meta["oem"],
                    "manufacturer": None,
                    "partnumber": None,
                    "category": None,
                    "description": f"Error de conexión, tras {retries} intentos fallidos",
                    "link": response.url,
                    "replaces": None,
                }
            return

        parts = response.css("td.listing-inner-content")

        if not parts:
            yield {
                "oem": response.meta["oem"],
                "manufacturer": None,
                "partnumber": None,
                "category": None,
                "description": "No se encontraron resultados",
                "link": response.url,
                "replaces": None,
            }

        for part in parts:
            yield {
                "oem": response.meta["oem"],
                "manufacturer": part.css("span.listing-final-manufacturer::text").get(),
                "partnumber": part.css("span.listing-final-partnumber::text").get(),
                "category": part.css("span.listing-footnote-text::text").get(),
                "description": part.css("span.span-link-underline-remover::text").get(),
                "link": response.url,
                "replaces": part.css(
                    'span[title="Reemplaza estos números alternativos/ números de Equipo Original"]::text'
                ).get(),
            }

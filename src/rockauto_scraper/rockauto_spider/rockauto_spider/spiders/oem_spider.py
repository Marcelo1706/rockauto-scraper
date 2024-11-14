import scrapy


class OemSpider(scrapy.Spider):
    name = "oem_spider"
    allowed_domains = ["rockauto.com"]
    max_retries = 3

    def __init__(self, oem_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oem_list = oem_list
        self.retries = {}

    def start_requests(self):
        for oem in self.oem_list:
            url = f"https://www.rockauto.com/es/partsearch/?partnum={oem}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "oem": oem,
                    "proxy": "http://127.0.0.1:24000",
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
                    "description": "No se pudo extraer los datos de la página, se ha excedido el número de intentos",
                    "link": response.url,
                    "replaces": None,
                }
            return

        parts = response.css("td.listing-inner-content")
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

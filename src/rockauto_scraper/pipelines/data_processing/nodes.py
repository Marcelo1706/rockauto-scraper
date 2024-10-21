"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.9
"""
import logging

import numpy as np
import pandas as pd
from scrapy import signals
from scrapy.crawler import Crawler, CrawlerProcess
from scrapy.utils.project import get_project_settings

from rockauto_scraper.rockauto_spider.rockauto_spider.spiders.oem_spider import (
    OemSpider,
)

logger = logging.getLogger(__name__)
items = []

def collect_items(item, response, spider):
    items.append(item)

def read_and_split_oem_data(data: pd.DataFrame, num_splits: int = 10) -> list:
    """
    Split the data into num_splits parts
    """
    oem_list = data['oem'].dropna().unique().tolist()
    split_data = np.array_split(oem_list, num_splits)

    return [list(part) for part in split_data]


def run_spiders_in_parallel(*oem_splits):
    oem_lists = list(oem_splits)
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    for oem_list in oem_lists:
        crawler = Crawler(OemSpider)
        crawler.signals.connect(collect_items, signal=signals.item_scraped)
        process.crawl(crawler, oem_list=oem_list)
        logger.info(f"Starting spider for {len(oem_list)} OEMs")

    process.start()
    logger.info(f"Items scraped: {len(items)}")
    return items


def consolidate_and_save_to_excel(scraping_results):
    # Convertir los resultados a un DataFrame
    consolidated_data = pd.DataFrame(scraping_results)

    # Asignar nombres a las columnas (si es necesario)
    consolidated_data.columns = [
        "OEM",
        "Manufacturer",
        "Part Number",
        "Category",
        "Description",
        "Link",
        "Replaces"
    ]

    return consolidated_data

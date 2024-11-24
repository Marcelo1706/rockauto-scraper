"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.9
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from pathlib import Path

import numpy as np
import pandas as pd
from azure.storage.blob import ContainerClient
from kedro.config import OmegaConfigLoader
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


def send_email_with_file_link(excel_output, recipient):
    conf_path = str(Path.cwd() / "conf")
    conf_loader = OmegaConfigLoader(conf_source=conf_path)
    credentials = conf_loader.get("credentials")
    smtp_credentials = credentials["smtp"]

    storage_account_name = "impressastorage"
    container_name = "results"
    container_client = ContainerClient.from_container_url(
        f"https://{storage_account_name}.blob.core.windows.net/{container_name}"
    )

    # Listar blobs en el contenedor para encontrar la versión más reciente
    blobs = container_client.list_blobs(name_starts_with="resultados.csv/")
    latest_blob = max(blobs, key=lambda b: b.name)

    file_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{latest_blob.name}"

    message = MIMEMultipart()
    message['From'] = smtp_credentials["user"]
    message['To'] = COMMASPACE.join(recipient)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = "RockAuto Scraper: Archivo Listo"

    message.attach(MIMEText(
        f"""
        Se adjunta el resultado del proceso de scraping de RockAuto.
        Fecha: {pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")}
        Enlace de descarga: {file_url}
        """
    ))

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_credentials["host"], smtp_credentials["port"]) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_credentials["user"], smtp_credentials["password"])
        server.sendmail(smtp_credentials["user"], recipient, message.as_string())

    logger.info("Email sent successfully")

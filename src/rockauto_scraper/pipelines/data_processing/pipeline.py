"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.9
"""

from kedro.pipeline import Pipeline, node

from .nodes import (
    consolidate_and_save_to_excel,
    read_and_split_oem_data,
    run_spiders_in_parallel,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=read_and_split_oem_data,
                inputs="oem_data",
                outputs=[f"oem_split_{i}" for i in range(10)],
                name="read_and_split_oem_data_node"
            ),
            node(
                func=run_spiders_in_parallel,
                inputs=[f"oem_split_{i}" for i in range(10)],
                outputs="scraping_results",
                name="run_spiders_in_parallel_node"
            ),
            node(
                func=consolidate_and_save_to_excel,
                inputs="scraping_results",
                outputs="excel_output",
                name="consolidate_and_save_to_excel_node"
            ),
        ]
    )

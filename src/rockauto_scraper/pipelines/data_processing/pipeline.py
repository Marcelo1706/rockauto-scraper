"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.9
"""

from kedro.pipeline import Pipeline, node

from .nodes import (
    consolidate_and_save_to_excel,
    read_and_split_oem_data,
    run_spiders_in_parallel,
    send_email_with_file_link,
    send_start_email,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=send_start_email,
                inputs=["params:recipient"],
                outputs="send_start_email_result",
                name="send_start_email_node"
            ),
            node(
                func=read_and_split_oem_data,
                inputs=["send_start_email_result", "oem_data"],
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
            node(
                func=send_email_with_file_link,
                inputs=["excel_output", "params:recipient"],
                outputs=None,
                name="send_email_with_file_link_node"
            )
        ]
    )

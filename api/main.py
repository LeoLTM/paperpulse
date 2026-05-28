import os
import pickle
import re
import logging

import urllib
import urllib.request as libreq

from datetime import datetime
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from api.utils import (
    extract_text_from_pdf, 
    extract_images_from_pdf_base64,
    download_pdf,
    add_markdown_links
    )
from api.arxiv_client import ArxivClient
from api.agent import PaperpulseAgent
from api.file_handler import FileHandler
from api.settings import load_config, build_arxiv_query, ARXIV_SORT_BY, ARXIV_SORT_ORDER

from api.webs import create_blogpost

logger = logging.getLogger(__name__)
logging.basicConfig(filename='myapp.log', level=logging.INFO)
logger.setLevel(logging.INFO)


def main():
    """
    Main function that orchestrates the retrieval and summarization process.
    """

    load_dotenv()
    dev_env=os.getenv("PROJECT_ENV")
    logger.info(dev_env)

    # load configuration
    config = load_config()
    search_query = build_arxiv_query(config)
    logger.info(f'ArXiv query: {search_query}')

    # initialise
    arxiv_client = ArxivClient(search_query, ARXIV_SORT_BY, ARXIV_SORT_ORDER)
    llm_agent = PaperpulseAgent(config)
    file_handler = FileHandler(os.getenv("PROJECT_DIR"))
    papers = None

    try:       
        # if in dev mode, check to see if papers were downloaded earlier

        if dev_env=='dev':
            papers = file_handler.load_papers()
        
        if not papers:        
            logger.info('Retrieving daily results')
            papers = arxiv_client.retrieve_daily_results()
        
            if dev_env=='dev':
                file_handler.save_papers(papers)
                
        if not papers:
            logger.error('No papers retrieved')
            return
        
        logger.info(f'Retrieved: {len(papers)} papers')

        summary = llm_agent.identify_important_papers(papers)
    except Exception as e:
        print(f'Exception: {e}')
        return

    # link papers mentioned in the summary to Arxiv
    summary_linked = add_markdown_links(summary, papers)

    # write the summary to a web page based on the day when the papers were retrieved
    create_blogpost(summary_linked, len(papers), config)

if __name__ == "__main__":
    main()


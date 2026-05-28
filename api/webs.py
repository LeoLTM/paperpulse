### Contains all of the code to take the summaries and 
### create the blog post and place in the correct directory
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def create_blogpost(summary, num_papers, config=None):
    """
    Creates a markdown file with specified naming convention and writes content.

    Args:
        summary (str): The summary content to write
        num_papers (int): Number of papers included in the summary
        config (dict): Paperpulse config loaded from config.yaml (optional)
    """
    if config is None:
        config = {}
    blog_cfg = config.get("blog", {})
    post_title = blog_cfg.get("post_title", "Daily Research Summary")

    todays_date = datetime.now().strftime('%Y-%m-%d')
    # Format the filename
    filename = f"{todays_date}-daily-summary.markdown"
    
    # Create the header with the current date
    header = f"""---
layout: post
title: {post_title}
date: {todays_date}
categories: summary
num_papers: {num_papers}
---
"""

    # Combine header and content
    full_content = f"{header}\n\n{summary}"
    
    # Write to file
    with open(os.path.join(os.getenv('PROJECT_DIR'),'blog/_posts/',filename), 'w') as file:
        file.write(full_content)
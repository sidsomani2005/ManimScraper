import scrapy
from markdownify import markdownify as md
import os

class StaticSpider(scrapy.Spider):
    name = 'static_spider'
    
    # Define the specific URLs to scrape
    start_urls = [
        'https://voiceover.manim.community/en/latest/installation.html',
        'https://voiceover.manim.community/en/latest/quickstart.html',
        'https://voiceover.manim.community/en/latest/services.html',
        'https://voiceover.manim.community/en/latest/translate.html',
        'https://voiceover.manim.community/en/latest/api.html',
    ]

    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Set to True to respect robots.txt
        'CONCURRENT_REQUESTS': 16,  # Adjust based on your needs
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,  # Introduce a slight delay
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'AUTOTHROTTLE_ENABLED': True,
        'HTTPCACHE_ENABLED': False,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'DEBUG',  # Use 'INFO' or 'DEBUG' for more verbosity
    }

    def __init__(self, *args, **kwargs):
        super(StaticSpider, self).__init__(*args, **kwargs)
        self.markdown_contents = []

    def parse(self, response):
        self.logger.debug(f"Parsing URL: {response.url} with status {response.status}")

        if response.status != 200:
            self.logger.error(f"Failed to retrieve {response.url} with status {response.status}")
            return

        # Use the correct CSS selector based on your inspection
        main_content = response.css('div#furo-main-content')  # Update this selector

        if not main_content:
            self.logger.warning(f"No main content found for {response.url}")
            return

        html_content = main_content.get()
        if not html_content.strip():
            self.logger.warning(f"Main content is empty for {response.url}")
            return

        # Convert HTML to Markdown using markdownify
        try:
            markdown = md(html_content, heading_style="ATX")
        except Exception as e:
            self.logger.error(f"Error converting HTML to Markdown for {response.url}: {e}")
            return

        # Extract the page title for the Markdown header
        page_title = response.css('h1::text').get(default='').strip()
        if not page_title:
            self.logger.warning(f"No title found for {response.url}")
            page_title = "Untitled Page"
        markdown_header = f"# {page_title}\n\n"

        full_markdown = markdown_header + markdown

        # Append to the list
        self.markdown_contents.append(full_markdown)
        self.logger.debug(f"Appended markdown for {response.url}")

    def closed(self, reason):
        self.logger.debug(f"Spider closed because: {reason}")
        output_path = os.path.join(os.getcwd(), 'manim_voiceover_docs.md')
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for content in self.markdown_contents:
                    f.write(content)
                    f.write("\n\n---\n\n")  # Separator between documents
            self.logger.info(f"Markdown file saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error writing to file {output_path}: {e}")

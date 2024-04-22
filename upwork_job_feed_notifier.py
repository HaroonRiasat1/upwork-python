import json
import logging
import os
import re
from datetime import datetime
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytz

import feedparser
import pandas as pd
import requests
import tzlocal
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
from selenium.webdriver.chrome.options import Options

#if you saved the key under a different environment variable name, you can do something like:
client = OpenAI(
  api_key="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",
)
# def scrape_job_activity(url):
#     # Set up Chrome options for headless mode
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Ensures Chrome runs in headless mode
#     chrome_options.add_argument("--window-size=1920x1080")  # Standard window size for desktop
#     chrome_options.add_argument("--disable-gpu")  # Recommended as per Selenium's documentation
#     chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, required on many platforms
#     chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

#     # Set up Chrome WebDriver
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     try:
#         driver.get(url)
#         driver.implicitly_wait(10)  # Optional: wait for JavaScript to load if necessary
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
#         activity_section = soup.find('section', {'data-test': "ClientActivity"})

#         if not activity_section:
#             print("Activity section not found.")
#             return {}
        
#         data = {}
#         items = activity_section.find_all('li', {'class': "ca-item"})
#         for item in items:
#             title = item.find('span', {'class': "title"}).text.strip().replace(':', '')
#             value = item.find('div', {'class': "value"}).text.strip() if item.find('div', {'class': "value"}) else item.find('span', {'class': "value"}).text.strip()
#             data[title] = value
        
#         return data
#     finally:
#         driver.quit()  # Make sure to quit the driver to free resources

# Main script execution
def generate_project_proposal(title, summary, skills, rate, link):
    prompt = f"Create proposal for the following project:\n\n" \
             f"Title: {title}\n" \
             f"Summary: {summary}\n" \
             f"Skills Required: {skills}\n" \
             f"Compensation: {rate}\n" \
             f"More Info: {link}\n\n" \
             f"Proposal:"
    template = f"""
    Hi,
    I have a PhD in CS from France and over 15+ years of experience in Software Development and Automation and specialize in the digital uplifting of organizations by replacing manual workflows with automation. I have automated dozens of workflows for my clients, saving them hundreds of hours in manual labor. For your project, I suggest using Google App script / Python Script, Google Calendar, DocuSign (automated Signing of documents by clients) and Make.com to glue everything together (can also be done in script). I have automated a number of similar workflows so am well suited for the job. I have extensive experience of automating workflows using custom developed Python, JavaScript and Google App script code, as well as automations using No Code platforms such as Make.com and Zapier.

    Some recent examples of automations that we have developed for our clients include:
    - Automating the process of creating PowerPoint pitches that contain advertising board information. The information is received in Email attachments as PDF documents, the relevant pieces of information are extracted, and the details are included in the generated PowerPoint presentation, that also includes information fetched from APIs such as Geo Path, Map images from Mapbox etc. The project is deployed on Microsoft Azure platform and involves Azure storage, Azure logics and Azure functions as main technology components. Third party applications such as Dropbox, are also integrated for data storage.
    - Automating invoicing for assistants provided to handicapped individuals for completing their office tasks. The automation developed in Python, integrates Google Calendar. Google Sheets, PDF form filling to generated time sheets and invoices for assistants. The invoices are then automatically signed and submitted for approval through DocuSign. Once signed, the completed forms are forwarded over email. Alerts are provided over Slack.
    - Automating onboarding of instructors, creating classes and course information using Jotforms, Google Sheets, Trello, Make.com and custom Python scripts for a mental health non-profit organization. The automation focused on end to end automations, including creating the courses, prepping the support materials, managing available instructors as well as posting on Trello boards for bidding by interested trainers.
    - Automating ETL pipeline for Email campaign using Airtable, Python code, Hunter.io, Double.io and Reeon, ChatGPT4. The work focused on automating enriching of lead information using LinkedIn Scraping of profiles, identifying of lead email information, processing and enriching the lead information using hunter.io and ChatGPT, verification and validation of lead contact information using hunter.io and Reeon. The automation was developed so that it could scale and handle tens of 1000s of leads per day and incorporate them in the Airtable lead database.

    I have excellent communication skills and always deliver high quality service. Looking forward to discussing the details with you in a meeting.
    """
    # Using chat completion to generate the proposal
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Please create proposal, you can use my tempelate:{template} "}
        ]
    )

    # Access the message directly and return the content
    # Ensure that the completion object has the expected structure
    return completion.choices[0].message.content

def generate_project_classification(title, summary, skills, rate, link):
    prompt = f"classify the following project:\n\n" \
             f"Title: {title}\n" \
             f"Summary: {summary}\n" \
             f"Skills Required: {skills}\n" \
             f"Compensation: {rate}\n" \
             f"More Info: {link}\n\n" \
             f"Proposal:"

    # Using chat completion to generate the proposal
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Please classify it into by returning only key word 'Web,Mobile,Automation,NodeCode,GenAi'"}
        ]
    )

    # Access the message directly and return the content
    # Ensure that the completion object has the expected structure
    return completion.choices[0].message.content

script_dir = os.path.dirname(os.path.abspath(__file__))
configs_file = os.path.join(script_dir, 'config.json')
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, filename=f'{script_dir}/upwork_scraper.log')
logger = logging.getLogger(__name__)

# Google Sheets setup
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('sub-q-400310-5228b332974c.json', scope)
gc = gspread.authorize(creds)

# Load configuration for Telegram
with open(configs_file, 'r') as f:
    config = json.load(f)

tgBotToken = config['tgBotToken']
bot_url = f'https://api.telegram.org/bot{tgBotToken}/'
chat_id = config['chat_id']

# Open the spreadsheet to read feed URLs
feed_url_sheet = gc.open('feed-url').sheet1
feed_urls = feed_url_sheet.col_values(1)  # Assuming URLs are in the first column

# Open or create the project-data document
try:
    project_data = gc.open('project-data')
except gspread.SpreadsheetNotFound:
    project_data = gc.create('project-data')

local_tz = tzlocal.get_localzone()
for feed_url in feed_urls:
    hash_object = hashlib.sha1(feed_url.encode())
    normalized_title = hash_object.hexdigest()[:100]

    try:
        worksheet = project_data.worksheet(normalized_title)
    except gspread.WorksheetNotFound:
        worksheet = project_data.add_worksheet(title=normalized_title, rows="1000", cols="20")
        headers = ["Job ID", "Title", "Category", "Rate", "Summary", "Link", "Posted On", "Country", "Skills", "Generate Proposal", "Proposal"]
        worksheet.append_row(headers)

    # Fetch existing job IDs to prevent duplicates
    existing_ids = worksheet.col_values(1)
    feed = feedparser.parse(feed_url)
    entries = []

    for entry in feed.entries:
        job_id = re.search(r'(?<=_)%([a-zA-Z0-9]+)', entry.link).group(1) if re.search(r'(?<=_)%([a-zA-Z0-9]+)', entry.link) else None
        if job_id and job_id in existing_ids:
            continue  # Skip if already exists

        # Entry details
        published_time = datetime.now(pytz.timezone("UTC")).strftime("%Y-%m-%d %H:%M")
        entry_data = [
            job_id, entry.title.replace(" - Upwork", ""),
            "Category", "Rate", "Summary",
            entry.link, published_time, "Country", "Skills",
            "No",  # Automatically set 'Generate Proposal' to 'Yes'
            ""  # Placeholder for proposal content
        ]

        # Generate proposal if required
        if worksheet.cell(existing_ids.index(job_id) + 1, 10).value == "Yes" if job_id in existing_ids else "Yes":
            proposal = generate_project_proposal(
                title=entry_data[1],
                summary=entry_data[4],
                skills=entry_data[8],
                rate=entry_data[3],
                link=entry_data[5]
            )
            entry_data[10] = proposal

        entries.append(entry_data)

    # Append new entries to the sheet
    if entries:
        worksheet.append_rows(entries, value_input_option='RAW')

logger.info('Google Sheet "project-data" has been updated with all feeds.')

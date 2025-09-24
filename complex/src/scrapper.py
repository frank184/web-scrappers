import os
import agentql
from playwright.sync_api import sync_playwright
from pyairtable import Api
from dotenv import load_dotenv

from aql.email      import EMAIL_QUERY
from aql.verify     import VERIFY_QUERY
from aql.password   import PASSWORD_QUERY
from aql.job_posts  import JOB_POSTS_QUERY
from aql.pagination import PAGINATION_QUERY

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

os.environ["AGENTQL_API_KEY"] = os.getenv('AGENTQL_API_KEY')

AIRTABLE_API_KEY    = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID    = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

BASE_URL = "https://www.idealist.org/"
LOGIN_FILE = "idealist_login.json"

def push_data_to_airtable(job_posts_data):
    airtable = Api(AIRTABLE_API_KEY)
    table = airtable.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

    # Push data to Airtable
    for job in job_posts_data:
        table.create(job)
    
    print(len(job_posts_data), "records pushed to Airtable")

def login():
    with sync_playwright() as playwright, playwright.chromium.launch(headless=False) as browser:
        page = agentql.wrap(browser.new_page())

        page.goto(BASE_URL) # Visit page

        # Use query_element() method to locate "Log In" button on the page
        email_input_response = page.query_elements(EMAIL_QUERY)
        email_input_response.login_form.email_input.fill(EMAIL)
        page.wait_for_timeout(1000) # (1s)

        # Verify human
        verify_response = page.query_elements(VERIFY_QUERY)
        verify_response.login_form.verify_not_robot_checkbox.click()
        page.wait_for_timeout(10000) # Wait long enough to complete Captcha (10s)

        # Continue next step
        email_input_response.login_form.continue_btn.click()

        # Input password
        password_response = page.query_elements(PASSWORD_QUERY)
        password_response.login_form.password_input.fill(PASSWORD)
        page.wait_for_timeout(1000) # (1s)
        password_response.login_form.continue_btn.click()

        # Wait for Login to complete
        page.wait_for_page_ready_state()

        # Save session for later use
        browser.contexts[0].storage_state(path=LOGIN_FILE)
        page.wait_for_timeout(10000) # (10s)

def main():
    if not os.path.exists(LOGIN_FILE):
        print("no login state found, logging in...")
        login()
    with sync_playwright() as playwright, playwright.chromium.launch(headless=False) as browser:
        context = browser.new_context(storage_state=LOGIN_FILE)
        page = agentql.wrap(context.new_page())

        page.goto(f"{BASE_URL}/en/jobs") # Visit page

        status = True
        while status:
            page.wait_for_page_ready_state()

            # Set current_url
            current_url = page.url

            # Fetch the job postings
            job_posts_response = page.query_elements(JOB_POSTS_QUERY)
            job_posts_data = job_posts_response.job_posts.to_data()

            print("Total number of job posts:", len(job_posts_data))

            # Write job posts to Airtable
            push_data_to_airtable(job_posts_data)

            pagingation_response = page.query_elements(PAGINATION_QUERY)
            next_page_btn = pagingation_response.pagination.next_page_btn
            next_page_btn.click()

            # Check if URL changed after next button click
            if current_url == page.url:
                status = False

        page.close()

if __name__ == '__main__':
    main()
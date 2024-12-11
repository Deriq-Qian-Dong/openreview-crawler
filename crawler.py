import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

def configure_driver():
    options = Options()
    options.add_argument("--headless")  # Headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Use webdriver-manager to configure Chromedriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def fetch_reviewer_scores(driver, base_xpath, review_index_start=2):
    """
    Dynamically fetch scores from all reviewers.
    :param driver: Selenium WebDriver
    :param base_xpath: Base XPath template with {N} as a placeholder for index
    :param review_index_start: Starting index for reviewer divs
    :return: List of scores from all reviewers
    """
    reviewer_scores = []
    review_index = review_index_start  # Start from the given index

    while True:
        try:
            # Generate dynamic XPath
            reviewer_xpath = base_xpath.replace("{N}", str(review_index))
            score_element = driver.find_element(By.XPATH, reviewer_xpath)
            reviewer_scores.append(score_element.text.split(':')[0])
            review_index += 1
        except:
            # Stop if no more reviewers are found
            break

    return reviewer_scores

def fetch_all_papers_with_scores(url):
    driver = configure_driver()
    driver.get(url)
    time.sleep(3)  # Wait for the page to load

    papers = []
    fail_count = 0
    failed_papers = []

    try:
        # Iterate through pagination, from page 3 to page 11
        for page in range(3, 12):
            print(f"Processing page {page - 2}")

            # Click on the pagination button
            try:
                page_xpath = f'//*[@id="accept"]/div/div/nav/ul/li[{page}]/a'
                driver.find_element(By.XPATH, page_xpath).click()
                time.sleep(1)  # Wait for the page to load
            except Exception as e:
                print(f"Failed to navigate to page {page - 2}: {e}")
                continue

            # Get all paper list items on the current page
            paper_elements = driver.find_elements(By.XPATH, '//*[@id="accept"]/div/div/ul/li')

            for i in tqdm(range(1, len(paper_elements) + 1), desc=f"Page {page - 2}"):
                paper_desc = ""

                # Construct dynamic XPath for each paper
                paper_xpath = f'//*[@id="accept"]/div/div/ul/li[{i}]/div/h4/a[1]'
                try:
                    # Click the paper link
                    link_element = driver.find_element(By.XPATH, paper_xpath)
                    driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
                    time.sleep(1)  # Wait for scrolling
                    
                    url = link_element.get_attribute("href")
                    driver.execute_script(f"window.open('{url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab

                    # driver.execute_script("arguments[0].click();", link_element)
                    time.sleep(1)  # Wait for the details page to load

                    # Fetch the title
                    try:
                        title_element = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div[1]/h2')
                        title = title_element.text
                    except:
                        title = "No title available"

                    # Fetch the track
                    try:
                        track_element = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div[4]/div[3]/span')
                        track = track_element.text
                    except:
                        try:
                            # //*[@id="content"]/div/div[1]/div[4]/div[4]/span
                            track_element = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div[4]/div[4]/span')
                            track = track_element.text
                        except:
                            track = "No track available"

                    # Fetch novelty scores
                    novelty_scores = fetch_reviewer_scores(driver, '//*[@id="forum-replies"]/div[{N}]/div[4]/div/div[6]/span')

                    # Fetch scope scores
                    scope_scores = fetch_reviewer_scores(driver, '//*[@id="forum-replies"]/div[{N}]/div[4]/div/div[5]/span')

                    # Fetch technical quality scores
                    technical_scores = fetch_reviewer_scores(driver, '//*[@id="forum-replies"]/div[{N}]/div[4]/div/div[7]/span')

                    # Save the paper information
                    papers.append({
                        "title": title,
                        "track": track,
                        "novelty_scores": novelty_scores,
                        "scope_scores": scope_scores,
                        "technical_scores": technical_scores
                    })

                    paper_desc = f"Title: {title[:30]} | Track: {track} | Novelty: {novelty_scores} | Scope: {scope_scores} | Technical: {technical_scores}"
                    tqdm.write(paper_desc)

                    # Return to the main page
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    fail_count += 1
                    failed_papers.append({
                        "page": page - 2,
                        "index": i,
                        "error": str(e)
                    })
                    tqdm.write(f"Error processing paper on page {page - 2}, index {i}: {e}")
                    continue


        return papers, fail_count, failed_papers

    finally:
        driver.quit()

# Save results to a CSV file
def save_to_csv(papers, filename="accepted_papers_with_scores.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "track", "novelty_scores", "scope_scores", "technical_scores"])
        writer.writeheader()
        for paper in papers:
            writer.writerow({
                "title": paper["title"],
                "track": paper["track"],
                "novelty_scores": ", ".join(paper["novelty_scores"]),
                "scope_scores": ", ".join(paper["scope_scores"]),
                "technical_scores": ", ".join(paper["technical_scores"])
            })

# Main execution
URL = "https://openreview.net/group?id=ACM.org/TheWebConf/2024/Conference#tab-accept"

papers, fail_count, failed_papers = fetch_all_papers_with_scores(URL)

# Print summary
print(f"Successfully fetched {len(papers)} papers.")
print(f"Failed to fetch {fail_count} papers.")
if failed_papers:
    print("Failed papers:")
    for failure in failed_papers:
        print(failure)

# Save to CSV
save_to_csv(papers)
print("Saved to accepted_papers_with_scores.csv")

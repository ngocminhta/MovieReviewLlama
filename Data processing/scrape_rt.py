import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

reviews_data = []
details_data = []

webdriver_service = Service(ChromeDriverManager().install())

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--disable-gpu")  
chrome_options.add_argument("--window-size=1920x1080")  
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument(f'user-agent={user_agent}')

class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome(service = webdriver_service, options=chrome_options)

    def crawl_reviews(self,movie):
        url = f'https://www.rottentomatoes.com/m/{movie}/reviews?type=user'
        self.driver.get(url)

        i = 0
        while i<10:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#reviews > div.load-more-container > rt-button'))
                )
                
                load_more_button.click()
                time.sleep(1)
                i += 1
            except Exception as e:
                print("Không còn trang để tải hoặc xảy ra lỗi:", e)
                break
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        movie_name = soup.find('a', class_='sidebar-title').text.strip()
        
        for review in soup.select('div.audience-review-row'):
            # Extract the rating
            rating = len(review.select('span.star-display__filled'))

            # Extract the review text
            review_text = review.select_one('p.audience-reviews__review').text.strip() if review.select_one('p.audience-reviews__review') else ''
                    
            reviews_data.append({
                'rating': rating,
                'review': review_text,
                'movie_name': movie_name
            })

        df2 = pd.DataFrame(reviews_data)
        df2.to_csv('rottentomatoes_reviews.csv', index=False)
        self.driver.quit()

    def crawl_details(self, movie):
        url = f'https://www.rottentomatoes.com/m/{movie}/reviews?type=user'
        self.driver.get(url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        movie_details = soup.find('ul', {'data-qa': 'sidebar-movie-details'})
        movie_name = soup.find('a', class_='sidebar-title').text.strip()
        
        # Extract movie detail
        if movie_details:
            list_items = movie_details.find_all('li')

            # Extract the duration (first <li> tag)
            duration = re.sub(r'[^a-zA-Z0-9_]', ' ', list_items[0].text.strip())
            duration = re.sub(r'  +', ' ', duration)
            duration = duration.replace('h', '').replace('m', '')
            duration = duration.split(' ')
            print(duration)
            if len(duration) == 2:
                movie_duration = int(duration[0])*60 + int(duration[1])
            elif len(duration) == 3:
                movie_duration = int(duration[1])*60 + int(duration[2])
            elif len(duration) == 4:
                movie_duration = int(duration[2])*60 + int(duration[3])
            elif len(duration) == 1 and duration[0]!='':
                movie_duration = int(duration[0])
            else:
                movie_duration = ''

            # Extract movie genre (assuming it's always the second <li> element)
            genre = list_items[1].text.strip()
            movie_genre = genre.split(',')[0]

            # Extract director 
            director = list_items[2].text.strip().replace(' ','')
            movie_director = director.split(':')[1].strip().replace('\n','')

            
            if 'In Theaters:' in list_items[3].text:
                release_text = list_items[3].text.replace('In Theaters:', '').strip()
                release_year_match = re.search(r'\b\d{4}\b', release_text)
                if release_year_match:
                    movie_release_year = release_year_match.group()
            elif 'Streaming:' in list_items[3].text:
                release_text = list_items[3].text.replace('Streaming:', '').strip()
                release_year_match = re.search(r'\b\d{4}\b', release_text)
                if release_year_match:
                    movie_release_year = release_year_match.group()
            else:
                movie_release_year = ''

        details_data.append({
            'movie_name': movie_name,
            'movie_duration': movie_duration,
            'movie_genre': movie_genre,
            'movie_director': movie_director,
            'movie_release_year': movie_release_year})
        
        df1 = pd.DataFrame(details_data)
        df1.to_csv('rottentomatoes_details.csv', index=False)

if __name__ == "__main__":
    list_movies = ['leave_no_trace', 'toy_story_2', 'man_on_wire', 'honeyland', 'sound_city', 'minding_the_gap', 'his_house', 'the_philadelphia_story', 
                   'crip_camp', '76_days', 'summer_1993', 'toy_story', 'the_tale_of_the_princess_kaguya', 'one_cut_of_the_dead', 'rewind_2020', 
                   'taxi_to_the_dark_side', 'welcome_to_chechnya', 'hive', 'deliver_us_from_evil', 'poetry', 'waste_land', 'the_square', 'coup_53', 
                   'the_terminator', 'the_janes', 'laura', 'stop_making_sense', 'stalker', 'playground', 'afghan_star', 'slalom', 'pinocchio', 
                   'local_hero', 'the_black_pirate', 'only_yesterday', 'merci_docteur_rey','athlete_a', 'tampopo', 'the_work', 'cool_hand_luke', 'last_train_home', 'one_missed_call', 
                   'left_behind', 'a_thousand_words', 'gotti', 'the_last_days_of_american_crime', 'jaws_the_revenge', 'the_ridiculous_6', 
                   'dark_crimes', 'stratton', 'london_fields', 'return_to_the_blue_lagoon', 'problem_child', 'cabin_fever', 'staying_alive', 
                   'the_disappointments_room', 'redline', 'homecoming', 'killing_me_softly', 'scar', 'beneath_the_darkness', 'max_steel', 
                   'cabin_fever', 'simon_sez', 'constellation', 'stolen', 'derailed', 'dark_tide', 'wagons_east', 'folks']
    
    # for movie in list_movies:
    #     scraper.crawl_details(movie)
    
    for movie in list_movies:
        scraper = Scraper()
        scraper.crawl_reviews(movie)
        

  
    

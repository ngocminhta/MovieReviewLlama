import numpy as np
import pandas as pd
from scrapy.selector import Selector
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import time
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")
import json
import os

webdriver_service = Service(ChromeDriverManager().install())

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--disable-gpu")  
chrome_options.add_argument("--window-size=1920x1080")  
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("accept-language=en-US,en")

class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome(service = webdriver_service, options=chrome_options)
        
    def crawl_reviews(self, movie_id, target, rating_range):
        review_collected = 0
        for rating in rating_range:
            if review_collected >= target:
                break
            url = f"https://www.imdb.com/title/{movie_id}/reviews?sort=curated&dir=desc&ratingFilter={rating}"
            time.sleep(1)
            self.driver.get(url)
            time.sleep(1)
            body = self.driver.find_element(By.CSS_SELECTOR, 'body')
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            body.send_keys(Keys.PAGE_DOWN)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            try:
                movie_name = soup.find('a', itemprop='url').get_text()
            except:
                movie_name = ''
                 
            for i in range(3):    
                try:    
                    self.driver.execute_script(f'''document.querySelector('#load-more-trigger').click()''')
                    time.sleep(3)
                except:
                    pass

            rating_list = []
            review_title_list = []
            review_list = []
            error_url_list = []
            error_msg_list = []
            reviews = self.driver.find_elements(By.CSS_SELECTOR, 'div.review-container')

            for d in tqdm(reviews):
                if review_collected >= target:
                    break
                try:
                    sel2 = Selector(text = d.get_attribute('innerHTML'))
                    try:
                        rating = sel2.css('.rating-other-user-rating span::text').extract_first()
                    except:
                        rating = np.NaN
                    try:
                        review = sel2.css('.text.show-more__control::text').extract_first()
                    except:
                        review = np.NaN    
                    try:
                        review_title = sel2.css('a.title::text').extract_first()
                    except:
                        review_title = np.NaN
                
                    rating_list.append(rating)
                    review_title_list.append(review_title)
                    review_list.append(review)
                    review_collected += 1

                except Exception as e:
                    error_url_list.append(url)
                    error_msg_list.append(e)
                    review_collected += 1
                

            review_df = pd.DataFrame({
                'rating':rating_list,
                'review':review_list,
                'movie_name':movie_name
                })
            
            file_path = 'imdb_review.csv'

            if os.path.isfile(file_path):
                review_df.to_csv(file_path, mode="a", index=False, header=False)
            else:
                review_df.to_csv(file_path, mode="a", index=False, header=True)

    def crawl_details(self, movie_id):
        url = f"https://www.imdb.com/title/{movie_id}/?ref_=tt_urv"
        time.sleep(1)
        self.driver.get(url)
        time.sleep(1)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        movie_title = soup.find('h1', {'data-testid': 'hero__pageTitle'}).get_text(strip=True)
        release_year = soup.find('ul', class_='ipc-inline-list ipc-inline-list--show-dividers sc-82970163-2 enBUqP baseAlt').find_all('li')[0].get_text(strip=True)
        try:
            duration = soup.find('ul', class_='ipc-inline-list ipc-inline-list--show-dividers sc-82970163-2 enBUqP baseAlt').find_all('li')[2].get_text(strip=True)
            duration = duration.split(' ')
            if len(duration) == 2:
                duration[0] = duration[0].replace('h', '')
                duration[1] = duration[1].replace('m', '')
                movie_duration = int(duration[0])*60 + int(duration[1])
            if len(duration) == 1:
                if 'h' in duration[0]:
                    duration[0] = duration[0].replace('h', '')
                    movie_duration = int(duration[0])*60
                else:
                    duration[0] = duration[0].replace('m', '')
                    movie_duration = int(duration[0])
        
        except:
            duration = soup.find('ul', class_='ipc-inline-list ipc-inline-list--show-dividers sc-82970163-2 enBUqP baseAlt').find_all('li')[1].get_text(strip=True)
            duration = duration.split(' ')
            if len(duration) == 2:
                duration[0] = duration[0].replace('h', '')
                duration[1] = duration[1].replace('m', '')
                movie_duration = int(duration[0])*60 + int(duration[1])
            if len(duration) == 1:
                if 'h' in duration[0]:
                    duration[0] = duration[0].replace('h', '')
                    movie_duration = int(duration[0])*60
                else:
                    duration[0] = duration[0].replace('m', '')
                    movie_duration = int(duration[0])

        imdb_rating = soup.find('div', {'data-testid': 'hero-rating-bar__aggregate-rating'}).find('span', class_='sc-bde20123-1').get_text(strip=True)
        genre_elements = soup.find_all('a', class_='ipc-chip')
        genres = [genre.get_text(strip=True) for genre in genre_elements]
        genres = str(genres[0])


        # Extract the director's name
        director_element = soup.find('a', href=lambda x: x and 'ref_=tt_ov_dr' in x)
        director_name = director_element.get_text(strip=True) 

        details_df = pd.DataFrame({
            'movie_name': movie_title,
            'movie_duration': movie_duration,
            'movie_genre': genres,
            'movie_director': director_name,
            'movie_release_year': release_year,
            }, index=[0])
        
        file_path = 'imdb_details.csv'

        if os.path.isfile(file_path):
            details_df.to_csv(file_path, mode="a", index=False, header=False, encoding='utf-8')
        else:
            details_df.to_csv(file_path, mode="a", index=False, header=True, encoding='utf-8')

    def get_movie_id(self):
        url = 'http://www.imdb.com/chart/top'
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        list_movies_id = []
        list_movies = soup.find('ul', class_='ipc-metadata-list ipc-metadata-list--dividers-between sc-9d2f6de0-0 iMNUXk compact-list-view ipc-metadata-list--base').find_all('li')
        for movie in list_movies:
            list_movies_id.append(movie.find('a').get('href').split('/')[2])
        
        return list_movies_id

if __name__ == "__main__":
    scraper = Scraper()
    list_movies_id = scraper.get_movie_id()
    
    for movie_id in list_movies_id:
        scraper.crawl_details(movie_id)
    
    for movie_id in list_movies_id:
        scraper.crawl_reviews(movie_id, 20, range(1, 6))
    
    for movie_id in list_movies_id:
        scraper.crawl_reviews(movie_id, 20, range(10,7,-1))
import time
import math
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from bs4 import BeautifulSoup


class RealtyParser:

    def __init__(self):
        self.url = "https://gkalliance.com.ua/catalog/?objecttype={realty_type}"
        self.realty_types = ["apartment", "secondary", "house", "land", "commercial", "town"]
        # self.realty_types = ["secondary"]
        self.driver = webdriver.Chrome()
        self.headers = {
            "Accept": "text/html",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }

    def start_parce(self) -> list:
        realty_data = list()
        realty_items_links = {f"{realty_type}": [] for realty_type in self.realty_types}

        first_iteration = True
        for realty_type in self.realty_types:
            self.driver.get(self.url.format(realty_type=realty_type))

            if first_iteration is True:
                try:
                    time.sleep(15)
                    pop_up_close_btn = self.driver.find_element(By.ID, "pop-up__close")
                    pop_up_close_btn.click()
                    print("form is closed")
                except ElementNotInteractableException:
                    print("form didn't appear")

            self.load_items()

            items_links = self.get_items_links()
            realty_items_links[realty_type] = items_links

            first_iteration = False

        self.driver.close()

        for realty_item_type, realty_item_links in realty_items_links.items():

            items_data = self.parce_items(item_links=realty_item_links, item_type=realty_item_type)
            realty_data.extend(items_data)

        return realty_data

    def load_items(self) -> None:
        try:
            number_of_items = self.driver.find_element(By.CLASS_NAME, "navigation__pages").text.split("-")[1].strip()
            pages = math.ceil(int(number_of_items) / 50)

            load_more_btn = self.driver.find_element(By.CLASS_NAME, "loadmore__btn")
            for i in range(pages - 1):
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
                load_more_btn.click()
                time.sleep(5)

        except IndexError:
            print("only one page")

    def get_items_links(self) -> list:
        item_links = list()
        items = self.driver.find_elements(By.CSS_SELECTOR, "div.objectList__item-mobDetails a")
        for item in items:
            item_link = item.get_attribute("href")
            item_links.append(item_link)

        return item_links

    def parce_items(self, item_links, item_type) -> list:
        print("start parce items")
        items_data = []

        for item_link in item_links:
            r = requests.get(url=item_link, headers=self.headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html5lib")

            item_data = dict()
            item_data["realty_type"] = item_type
            item_data["title"] = soup.find("span", {"class": "breadcrumbs__current"}).get_text(strip=True)

            description_paragraphs = soup.find("div", {"class": "default__description"}).find_all("p")
            item_data["description"] = "\n\n".join(p.get_text(strip=True) for p in description_paragraphs)

            price_element = soup.find("div", {"class": "singleObject__info-price"})
            item_data["price"] = int(
                price_element.get_text(strip=True).replace(" ", "").replace("$", "")) if price_element else None

            item_data["images"] = [image.get("href") for image in
                                   soup.find_all("a", {"class": "singleObject__sliderItem"})]

            item_data.update({li.attrs["class"][-1].replace("-", " ").split()[-1]: li.get_text(strip=True)
                              for li in soup.find("ul", {"class": "singleObject__info-list"}).find_all("li")})

            seller_data = dict()
            seller_data["name"] = soup.find("div", {"class": "singleObject__manager-contactsName"}).get_text(strip=True)
            seller_contacts = soup.find("div", {"class": "singleObject__manager-contactsPhones"})
            seller_data["contacts"] = [contact.get_text(strip=True).replace(" ", "")
                                       for contact in seller_contacts.find_all("a", href=True)]
            seller_data["image"] = soup.find("div", {"class": "singleObject__manager-photo"}).find("img").get("src")

            item_data["seller_data"] = seller_data

            items_data.append(item_data)
        return items_data

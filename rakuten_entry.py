from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import numpy as np
from scipy.stats import truncnorm
import keyring
from keyring.credentials import Credential
from rich import print

import time


def main():
    cred = keyring.get_credential("rakuten", None)
    assert cred is not None, "credential information for rakuten is not registerd."

    driver = webdriver.Chrome()

    login(driver, cred)
    wait_random_time(0.0, 4.0, 1.0)

    entry_campaigns(driver, cred)

    click_point(driver)

    driver.quit()


def login(driver: WebDriver, cred: Credential):
    driver.get(
        "https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml?l-id=enavi_all_glonavi_campaign")
    wait_random_time(3.0, 1.0, 1.0)

    # login
    elem: WebElement = driver.find_element("id", "u")
    elem.send_keys(cred.username)
    elem = driver.find_element("id", "p")
    elem.send_keys(cred.password)
    elem.submit()


def entry_campaigns(driver: WebDriver, cred: Credential):
    elem = driver.find_element("id", "ongoingCampaign")
    campaign_ids: list[str] = elem.get_attribute(
        "data-campaign-codes").split(" ")

    # get campaign list
    campaign_info = []
    for cid in campaign_ids:
        article: WebElement = driver.find_element("id", cid)
        campaign_info.append({
            "cid": cid,
            "entry_necessary": article.get_attribute(
                "data-entry-necessary") == "true",
            "applied": article.get_attribute("data-applied-flag") == "true",
            "campaign_name": article.get_attribute("data-campaign-name")
        })

    # entry each campaign
    for d in campaign_info:
        print(d)

        if d["entry_necessary"] and not d["applied"]:
            driver.get(
                "https://www.rakuten-card.co.jp/e-navi/members/campaign/entry.xhtml?camc="+d["cid"])
            wait_random_time(5.0, 1.5, 1.0)

            entry_button: Optional[WebElement] = None
            for button_id in ("entryForm:entry",  "entryForm:entryTeam"):
                try:
                    entry_button = driver.find_element(
                        "id", button_id)
                except NoSuchElementException:
                    continue
                break

            if entry_button is None:
                print(
                    f"*****{d['campaign_name']} is not entried but not applied.*****")
                continue

            entry_button.click()
            wait_random_time(5.0, 1.0, 1.0)
            print("applied!")


def click_point(driver: WebDriver):
    # click point
    driver.get("https://www.rakuten-card.co.jp/e-navi/members/point/click-point/index.xhtml?l-id=enavi_mtop_pointservice_click")
    wait_random_time(3.0, 1.0, 1.0)

    boxes = driver.find_elements(
        By.CSS_SELECTOR, "div.topArea.clearfix div.bnrBoxInner")
    num_boxes = len(boxes)
    for i in range(num_boxes):
        box = driver.find_elements(
            By.CSS_SELECTOR, "div.topArea.clearfix div.bnrBoxInner")[-i-1]
        link: WebElement = box.find_element(By.CSS_SELECTOR, "a")
        link.click()
        wait_random_time(5.0, 1.0, 1.0)
        driver.switch_to.window(driver.window_handles[0])


def wait_random_time(loc: float, scale: float, least: float):
    s = truncnorm.rvs(least, np.inf, loc, scale)
    time.sleep(s)


if __name__ == "__main__":
    main()

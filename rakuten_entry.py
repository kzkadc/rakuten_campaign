from typing import Optional
import time

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


def main():
    cred = keyring.get_credential("rakuten", None)
    assert cred is not None, "credential information for rakuten is not registerd."

    driver = webdriver.Chrome()

    login(driver, cred)
    wait_random_time(4.0, 2.0, 2.0)

    entry_campaigns(driver)

    entry_pointcard_campaign(driver)

    click_point(driver)

    driver.quit()


def login(driver: WebDriver, cred: Credential):
    driver.get(
        "https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml?l-id=enavi_all_glonavi_campaign")
    wait_random_time(4.0, 1.0, 2.0)

    # login
    elem: WebElement = driver.find_element("id", "u")
    elem.send_keys(cred.username)
    elem = driver.find_element("id", "p")
    elem.send_keys(cred.password)
    elem.submit()


def entry_campaigns(driver: WebDriver):
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
            wait_random_time(5.0, 2.0, 3.0)

            entry_button: Optional[WebElement] = None
            for button_id in ("entryForm:entry",  "entryForm:entryTeam"):
                entry_button = find_element(driver, By.ID, button_id)
                if entry_button is None:
                    continue
                else:
                    break

            if entry_button is None:
                entry_button = find_element(
                    driver,
                    By.CSS_SELECTOR,
                    ".user-friendly-campaign-entry-form-entry-button-area"
                )

            if entry_button is None:
                print(
                    f"*****{d['campaign_name']} is not entried but not applied.*****")
            else:
                try:
                    entry_button.click()
                except Exception as e:
                    print(f"cannot entry: {e}")
                else:
                    print("applied!")

                wait_random_time(5.0, 2.0, 3.0)


def entry_pointcard_campaign(driver: WebDriver):
    driver.get("https://pointcard.rakuten.co.jp/campaign/")

    wait_random_time(5.0, 2.0, 3.0)

    SCROLL_STEPS = 4
    for i in range(1, SCROLL_STEPS + 1):
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight*{i}/{SCROLL_STEPS});")
        wait_random_time(2.0, 1.0, 1.0)

    wait_random_time(5.0, 2.0, 3.0)

    campaign_elems = driver.find_elements(
        By.CSS_SELECTOR, "li.Campaign__root.Campaign__show")
    campaign_info = []
    for elem in campaign_elems:
        details = elem.find_element(By.CSS_SELECTOR, ".Campaign__details")
        name = details.find_element(By.CSS_SELECTOR, ".Campaign__title")
        name = name.text.strip()

        state = details.find_element(
            By.CSS_SELECTOR, ".Badges__root")
        state = state.text.strip()

        url = elem.find_element(By.CSS_SELECTOR, "a.Campaign__contents") \
            .get_attribute("href")

        campaign_info.append((name, state, url))

    for name, state, url in campaign_info:
        print(f"{name}, {state}, {url}")
        if any(w in state for w in ("エントリー不要", "エントリー済")):
            print("-- skip")
            continue

        driver.get(url)
        wait_random_time(5.0, 2.0, 3.0)
        entry_button = find_element(driver, By.CSS_SELECTOR,
                                    ".rex-entry-button__enabled a")
        if entry_button is not None:
            try:
                entry_button.click()
            except Exception as e:
                print(f"-- could click entry button: {e}")
            wait_random_time(5.0, 2.0, 3.0)
        else:
            print("-- could not find entry button")


def find_element(driver: WebDriver, by: str, val: str) -> WebElement | None:
    try:
        elem = driver.find_element(by, val)
    except NoSuchElementException:
        return None

    return elem


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
        wait_random_time(5.0, 1.0, 3.0)
        driver.switch_to.window(driver.window_handles[0])


def wait_random_time(loc: float, scale: float, least: float):
    a = (least - loc) / scale
    s = truncnorm.rvs(a, np.inf, loc, scale)
    time.sleep(s)


if __name__ == "__main__":
    main()

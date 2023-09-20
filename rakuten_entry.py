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
from rich import print  # pylint: disable=W0622


def main():
    cred = keyring.get_credential("rakuten", None)
    assert cred is not None, "credential information for rakuten is not registerd."

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    login(driver, cred)
    wait_random_time(4.0, 2.0, 2.0)

    entry_point_plus(driver)

    entry_campaigns(driver)

    entry_pointcard_campaign(driver)

    entry_pay_campaign(driver)

    click_point(driver)

    driver.quit()


def login(driver: WebDriver, cred: Credential):
    driver.get(
        "https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml?l-id=enavi_all_glonavi_campaign")
    wait_random_time(4.0, 1.0, 2.0)

    # login
    elem = driver.find_element(By.ID, "u")
    elem.send_keys(cred.username)
    elem = driver.find_element(By.ID, "p")
    elem.send_keys(cred.password)
    elem.submit()


def entry_campaigns(driver: WebDriver):
    driver.get(
        "https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml?l-id=enavi_all_glonavi_campaign")
    wait_random_time(4.0, 1.0, 2.0)

    elem = driver.find_element(By.ID, "ongoingCampaign")
    campaign_ids = elem.get_attribute("data-campaign-codes")
    if campaign_ids is None:
        print("could not get campaign_ids")
        return
    campaign_ids = campaign_ids.split(" ")

    # get campaign list
    campaign_info = []
    for cid in campaign_ids:
        article = driver.find_element(By.ID, cid)
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
                "https://www.rakuten-card.co.jp/e-navi/members/campaign/entry.xhtml?camc=" + d["cid"])
            wait_random_time(5.0, 2.0, 3.0)

            entry_button = None
            for button_id in ("entryForm:entry", "entryForm:entryTeam"):
                entry_button = find_element(driver, By.ID, button_id)
                if entry_button is None:
                    continue
                break

            if entry_button is None:
                entry_button = find_element(
                    driver, By.CSS_SELECTOR,
                    ".user-friendly-campaign-entry-form-entry-button-area"
                )

            if entry_button is None:
                print(
                    f"*****{d['campaign_name']} is not entried but not applied.*****")
            else:
                try:
                    driver.execute_script(
                        "arguments[0].click();", entry_button)
                except Exception as e:
                    print(f"cannot entry: {e}")
                else:
                    print("applied!")

                wait_random_time(5.0, 2.0, 3.0)


def entry_point_plus(driver: WebDriver):
    driver.get("https://www.rakuten-card.co.jp/e-navi/members/point/shop-point/index.xhtml?l-id=enavi_oo_pointservice_xlo_sideguide")

    wait_random_time(5.0, 2.0, 3.0)

    components = driver.find_elements(
        By.CSS_SELECTOR, "div[data-state=\"undone\"] a.xlo-mfp-btn-ajax.xlo-tab-store-item")

    for c in components:
        try:
            driver.execute_script("arguments[0].click();", c)
        except Exception as e:
            print(f"-- could not click component: {e}")
            continue

        wait_random_time(5.0, 2.0, 3.0)

        entry_button = find_element(
            driver,
            By.CSS_SELECTOR,
            "div.mfp-container div#mfp .xlo-new-btn-primary.xlo-new-btn-pill.xlo-btn-primary--undone"
        )
        if entry_button is None:
            print("could not find entry button")
            continue

        store_name = find_element(
            driver, By.CSS_SELECTOR, "div.mfp-container div#mfp .xlo-new-mfp__store-name")
        if store_name is None:
            print("store name unrecognized")
        else:
            print(store_name.text.strip())

        driver.execute_script("arguments[0].click();", entry_button)

        wait_random_time(5.0, 2.0, 3.0)


def entry_pay_campaign(driver: WebDriver):
    driver.get("https://pay.rakuten.co.jp/campaign/")

    wait_random_time(5.0, 2.0, 3.0)

    campaign_list = driver.find_elements(
        By.CSS_SELECTOR, ".rpay-cmp ul#js-cmp-view-list.r-cp-list a.active")

    campaign_info = []
    for cmp in campaign_list:
        name = find_element(cmp, By.CSS_SELECTOR,
                            ".r-cp-list-cont .r-cp-title")
        if name is None:
            continue

        name = name.text.strip()
        url = cmp.get_attribute("href")
        if url is None:
            continue

        url = url.strip()
        need_to_entry = find_element(
            cmp, By.CSS_SELECTOR, ".r-cp-bnr-icon-no-need-to-enter") is None
        campaign_info.append({
            "name": name,
            "url": url,
            "need_to_entry": need_to_entry
        })

    wait_random_time(5.0, 2.0, 3.0)

    BUTTON_SELECTOR_PARENTS = (
        "div.CampaignButton",
        "div.user-friendly-campaign-entry-form-entry-button-area",
        "div.rex-entry-button__enabled"
    )
    BUTTON_SELECTOR = f":is({','.join(BUTTON_SELECTOR_PARENTS)}) a"

    for cmp in campaign_info:
        print(cmp["name"])
        if not cmp["need_to_entry"]:
            print("-- no need to entry")
            continue

        driver.get(cmp["url"])

        wait_random_time(5.0, 2.0, 3.0)

        button = find_element(driver, By.CSS_SELECTOR,
                              BUTTON_SELECTOR)
        if button is None:
            print("-- Could not find entry button")
            continue

        try:
            driver.execute_script("arguments[0].click();", button)
        except Exception as e:
            print(f"-- Could not entry: {e}")
            continue

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
                driver.execute_script("arguments[0].click();", entry_button)
            except Exception as e:
                print(f"-- could not click entry button: {e}")
            wait_random_time(5.0, 2.0, 3.0)
        else:
            print("-- could not find entry button")

        print()


def click_point(driver: WebDriver):
    # click point
    driver.get("https://www.rakuten-card.co.jp/e-navi/members/point/click-point/index.xhtml?l-id=enavi_mtop_pointservice_click")
    wait_random_time(3.0, 1.0, 1.0)

    boxes = driver.find_elements(
        By.CSS_SELECTOR, "div.topArea.clearfix div.bnrBoxInner")
    for i, _ in enumerate(boxes):
        box = driver.find_elements(
            By.CSS_SELECTOR, "div.topArea.clearfix")[-i - 1]

        try:
            box.find_element(By.CSS_SELECTOR, ".dateArrival img")
        except NoSuchElementException:
            print(f"continue: {i}")
            continue

        link = box.find_element(By.CSS_SELECTOR, ".bnrBoxInner a")
        driver.execute_script("arguments[0].click();", link)

        wait_random_time(5.0, 1.0, 3.0)
        driver.switch_to.window(driver.window_handles[0])


def find_element(driver: WebDriver | WebElement,
                 by: str, val: str) -> WebElement | None:
    try:
        elem = driver.find_element(by, val)
    except NoSuchElementException:
        return None

    return elem


def wait_random_time(loc: float, scale: float, least: float):
    a = (least - loc) / scale
    s = truncnorm.rvs(a, np.inf, loc, scale)
    time.sleep(s)


if __name__ == "__main__":
    main()

import time
import json

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

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

    entry_functions = (
        entry_point_plus,
        entry_campaigns,
        entry_pointcard_campaign,
        entry_fashion,
        click_point
    )
    for i in np.random.permutation(len(entry_functions)):
        entry_functions[i](driver)

    driver.quit()

    print("Finished")


def login(driver: WebDriver, cred: Credential):
    driver.get(
        "https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml?l-id=enavi_all_glonavi_campaign")
    wait_random_time(4.0, 1.0, 2.0)

    # login
    elem = driver.find_element(By.ID, "user_id")
    elem.send_keys(cred.username)
    wait_random_time(2.0, 1.0, 1.0)
    button = driver.find_element(By.CSS_SELECTOR, "#cta001 > div > div")
    driver.execute_script("arguments[0].click();", button)

    wait_random_time(3.0, 1.0, 2.0)

    elem = driver.find_element(By.ID, "password_current")
    elem.send_keys(cred.password)
    wait_random_time(2.0, 1.0, 1.0)
    button = driver.find_element(By.CSS_SELECTOR, "#cta011 > div > div")
    driver.execute_script("arguments[0].click();", button)


def entry_campaigns(driver: WebDriver):
    print("Campaigns")

    driver.get("https://www.rakuten-card.co.jp/e-navi/members/campaign/index.xhtml"
               "?l-id=enavi_all_glonavi_campaign")
    wait_random_time(4.0, 1.0, 2.0)

    campaign_ids = driver.find_element(
        By.CSS_SELECTOR, "#user-basic-info").get_attribute("value")
    if campaign_ids is None:
        print("could not get campaign_ids")
        return

    campaign_ids = json.loads(campaign_ids)
    campaign_ids = campaign_ids["items"]["campaign_status"]["ongoing"]["unregistered"]
    print("campaign_ids", campaign_ids)

    shuffled_campaign_ids_it = (
        campaign_ids[i]
        for i in np.random.permutation(len(campaign_ids))
    )

    # entry each campaign
    for cid in shuffled_campaign_ids_it:
        print(cid)

        driver.get(
            "https://www.rakuten-card.co.jp/e-navi/members/campaign/entry.xhtml?camc=" + cid)
        wait_random_time(5.0, 2.0, 3.0)

        if any(
            driver.current_url.startswith(url)
            for url in (
                "https://www.rakuten-card.co.jp/e-navi/members/point/shop-point",
                "https://pay.rakuten.co.jp/campaign",
                "https://pointcard.rakuten.co.jp/campaign"
            )
        ):
            continue

        entry_button = None
        for button_id in ("entryForm:entry", "entryForm:entryTeam"):
            entry_button = find_element(driver, By.ID, button_id)
            if entry_button is None:
                continue
            break

        if entry_button is None:
            ENTRY_BUTTON_PARENTS = (
                ".rex-entry-button__enabled",
                ".CampaignButton",
                ".user-friendly-campaign-entry-form-entry-button-area",
                ".applyBtnWrap",
                ".rcEntryButton-button"
            )
            ENTRY_BUTTON_SELECTOR = f":is({','.join(
                ENTRY_BUTTON_PARENTS)}) a"

            entry_button = find_element(
                driver, By.CSS_SELECTOR, ENTRY_BUTTON_SELECTOR)

        if entry_button is None or "エントリー済" in entry_button.text:
            print(f"*****{cid} is not entried but not applied,"
                  " or has already been entried.*****")
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
    print("Point Plus")

    driver.get("https://www.rakuten-card.co.jp/e-navi/members/point/shop-point/index.xhtml"
               "?l-id=enavi_oo_pointservice_xlo_sideguide")

    wait_random_time(5.0, 2.0, 3.0)

    card_select = driver.find_element(
        By.CSS_SELECTOR, "#cardChangeForm select")
    card_select = Select(card_select)

    shuffled_card_idx_it = np.random.permutation(len(card_select.options))

    for card_index in shuffled_card_idx_it:
        card_select = driver.find_element(
            By.CSS_SELECTOR, "#cardChangeForm select")
        card_select = Select(card_select)

        card_select.select_by_index(card_index)
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


def entry_pointcard_campaign(driver: WebDriver):
    print("Pointcard Campaign")

    driver.get("https://pointcard.rakuten.co.jp/campaign/")

    wait_random_time(5.0, 2.0, 3.0)

    def get_campaigns() -> list[dict[str, str]]:
        """
        returns: [{"url": "https://...", "name": "campaign name"}, ...]
        """

        nonlocal driver

        campaigns = []

        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "article.medias-grid a.card"
        )

        for card in cards:
            # カード内のラベルを取得
            labels = card.find_elements(
                By.CSS_SELECTOR,
                ".card__labels .label"
            )

            label_texts = {label.text.strip() for label in labels}

            # 対象のキャンペーンだけ抽出
            if not label_texts.intersection({"未エントリー", "ページで確認"}):
                continue

            url = card.get_attribute("href")

            title = card.find_element(
                By.CSS_SELECTOR,
                ".card__title"
            ).text.strip()

            campaigns.append({
                "url": url,
                "name": title,
            })

        return campaigns

    campaign_info = get_campaigns()
    shuffled_campaign_it = (
        campaign_info[i]
        for i in np.random.permutation(len(campaign_info))
    )

    ENTRY_BUTTON_PARENTS = (
        ".rex-entry-button__enabled",
        ".CampaignButton",
        ".user-friendly-campaign-entry-form-entry-button-area"
    )
    ENTRY_BUTTON_SELECTOR = f":is({','.join(ENTRY_BUTTON_PARENTS)}) a"

    for camp_dict in shuffled_campaign_it:
        name = camp_dict["name"]
        url = camp_dict["url"]

        print(f"{name}, {url}")

        driver.get(url)
        wait_random_time(5.0, 2.0, 3.0)
        entry_button = find_element(driver, By.CSS_SELECTOR,
                                    ENTRY_BUTTON_SELECTOR)
        if entry_button is not None \
                and "エントリー済" not in entry_button.text:

            try:
                driver.execute_script("arguments[0].click();", entry_button)
            except Exception as e:
                print(f"-- could not click entry button: {e}")
            wait_random_time(5.0, 2.0, 3.0)
        else:
            print("-- could not find entry button or has already been entried")

        print()


def entry_fashion(driver: WebDriver):
    print("Fashion")

    driver.get("https://brandavenue.rakuten.co.jp/contents/o2o-entry/spu/")
    wait_random_time(3.0, 1.0, 1.0)

    cards = driver.find_elements(
        By.CSS_SELECTOR, ".o2o-entry-card-list .o2o-entry-card")
    card_order = np.random.permutation(len(cards))
    for i in card_order:
        cards = driver.find_elements(
            By.CSS_SELECTOR, ".o2o-entry-card-list .o2o-entry-card")
        card = cards[i]

        if "エントリー済み" in card.text:
            continue

        try:
            link = card.find_element(
                By.CSS_SELECTOR, "button.o2o-entry-card-info-action")
            name = card.get_attribute("data-brandname")
        except NoSuchElementException:
            print("cannot entry")
            continue

        driver.execute_script("arguments[0].click();", link)
        print(name)

        wait_random_time(2.0, 1.0, 1.0)


def click_point(driver: WebDriver):
    print("Click point")

    # click point
    driver.get("https://www.rakuten-card.co.jp/e-navi/members/point/click-point/index.xhtml"
               "?l-id=enavi_top_info-personal_click-point")
    wait_random_time(3.0, 1.0, 1.0)

    try:
        banners = driver.find_elements(
            By.CSS_SELECTOR, "#js-click-point-banner-list li a")
    except NoSuchElementException:
        print("No banners.")
        return

    print(f"Number of banners: {len(banners)}")

    shuffled_banner_it = (
        banners[i]
        for i in np.random.permutation(len(banners))
    )

    for b in shuffled_banner_it:
        if "獲得済" in b.text:
            continue

        driver.execute_script("arguments[0].click();", b)

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

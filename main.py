from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver import FirefoxProfile


import requests as rq
import time
import json
from XPaths import ProfilePage, MainPage, ReelPage
from time import sleep
from typing import TypedDict
from random import shuffle, choice, randint
from os.path import exists
import os
from datetime import datetime
from subprocess import check_output

'''
{
    "targetUser":"dailyoriginalmusic",
    "accountInteractionInterval":5,
    "reelInteractionInterval":1,
    "realWatchDuration":3,
    "like":true,
    "likeRangeMinimum":0,
    "likeRangeMaximum":10,
    "share":true,
    "shareRangeMinimum":0,
    "shareRangeMaximum":10,
    "comment":true,
    "commentRangeMinimum":0,
    "commentRangeMaximum":10,
    "search":true,
    "maxNumberOfReelsToWatch":30,
    "specificReelIDsToWatch": [],
    "usersToShareTo":[],
    "proxies":[

    ],
    "accounts":[
        {
            "username":"bruhhhhhhhh786",
            "password":"otaku$123"
        }
    ]
}'''

class Account(TypedDict):
    username:str
    password:str

class Config(TypedDict):
    targetUser:str
    interactionInterval:int
    accountInteractionInterval:int
    reelInteractionInterval:int
    individualInteractionInterval:int
    like:bool
    likeRangeMinimum:int
    likeRangeMaximum:int
    share:bool
    shareRangeMinimum:int
    shareRangeMaximum:int
    comment:bool
    commentRangeMinimum:int
    commentRangeMaximum:int
    search:bool
    maxNumberOfReelsToWatch:int
    specificReelIDsToWatch: list[str]
    usersToShareTo: list[str]
    proxies: list[str]
    accounts: list[Account]
    useProxy:bool

LOG_FILE = "logs.txt"
COMMENTS_FILE = "comments.txt"
SHARE_MESSAGES_FILE = "shareMessages.txt"


GECKODRIVER_WINDOWS_LINK = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-win32.zip"
GECKODRIVER_LINUX_LINK = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz"

GECKODRIVER_LOCATION = "driver\\geckodriver.exe"
FIREFOX_BINARY_LOCATION = "firefox\\firefox.exe"


def log(printAsWell, msg):
    if not exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(f"{datetime.now()} ===> Created Log file.\n")
        return
    
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} ===> {msg}\n")
    
    if printAsWell:
        print(f"{datetime.now()} ===> {msg}")


class ViewBot:
    def __init__(self, driver:webdriver.Firefox, config:Config, username = "", password = "", verbose = True):
        self.driver:webdriver.Firefox = driver
        self.verbose = verbose
        self.username, self.password = username, password
        self.standardWait = 10

        if verbose:
            log(self.verbose, config)    

        self.instaBaseURL = "https://instagram.com/"

        self.standardWait += getPing() / 1000

        self.isLoggedIn = False
        self.navigatedToUser = False
        self.currentReelID = None

        driver.get(self.instaBaseURL)
    

    def login(self) -> bool:
        try:

            if self.verbose:
                log(self.verbose, "Sending password details.")
            # Find and fill the username field
            username_field = WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(self.username)

            # Find and fill the password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(self.password)

            # Submit the login form
            password_field.send_keys(Keys.RETURN)

            if self.verbose:
                log(self.verbose, "Login details sent. Waiting for login")
            
            
            # Wait until the main page loads by checking for an element that appears on the main page
            try:
                WebDriverWait(self.driver, self.standardWait).until(
                    EC.presence_of_element_located((By.XPATH, MainPage["saveLoginNotNowButton"]))
                )
            except NoSuchElementException:
                try:
                    suspiciousBehavourButton = self.driver.find_element(By.XPATH, MainPage["suspectedBehaviour"])
                    suspiciousBehavourButton.click()
                except Exception as e:
                    log(self.verbose, str(e))
                    return False
            if self.verbose:
                log(self.verbose, "Login successful")

            notNowButton = self.driver.find_element(By.XPATH, MainPage["saveLoginNotNowButton"])
            notNowButton.click()

            
            try:
                WebDriverWait(self.driver, self.standardWait).until(
                    EC.presence_of_element_located((By.XPATH, MainPage["notificationNotNowButton"]))
                )
            except NoSuchElementException:
                if self.verbose:
                    log(self.verbose, "Did not get notification message")
        
            if self.verbose:
                log(self.verbose, "Login successful. Passed notifications alert.")

            notNowButton = self.driver.find_element(By.XPATH, MainPage["notificationNotNowButton"])
            notNowButton.click()
            

            self.isLoggedIn = True            
            return True

        except Exception as e:
            if self.verbose:
                log(self.verbose, f"An error occurred during login: {e}")
            return False

    def searchAndNavigateToTargetUser(self) -> bool:
        try:
            if self.verbose:
                log(self.verbose, "Starting search")
            # Click the search button
            search_button = WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, MainPage["searchButton"]))
            )
            search_button.click()

            # Enter the query into the search bar
            search_bar = WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, MainPage["searchBar"]))
            )
            search_bar.send_keys(config["targetUser"])
            search_bar.send_keys(Keys.RETURN)


            if self.verbose: log(self.verbose, "Waiting for search results.")
            # Wait for search results to load
            WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, MainPage["searchedUsersContainer"]))
            )

            search_container = self.driver.find_element(By.XPATH, MainPage["searchedUsersContainer"])
            
            if self.verbose: log(self.verbose, "Waiting for target's search result.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, MainPage["firstSearchResult"]))
            )
            
            if self.verbose:
                log(self.verbose, "Going to user profile page")

            
            try:
                user_profile_search_result = search_container.find_element(By.XPATH, MainPage["firstSearchResult"])
                
                if self.verbose:
                    log(self.verbose, f"Search for '{config['targetUser']}' completed successfully")
                
                user_profile_search_result.click()
            except StaleElementReferenceException as e:
                log(self.verbose, "Stale element reference to first search result. Directly switching to reels page.")
                self.driver.get(f"{self.instaBaseURL}{config['targetUser']}")
            
            try:
                WebDriverWait(self.driver, self.standardWait).until(
                    EC.presence_of_element_located((By.XPATH, ProfilePage["username"]))
                )
            except NoSuchElementException as e:
                log(self.verbose, "Did not find username.")
            if self.verbose:
                log(self.verbose, f"Navigated to target user {config['targetUser']} profile page.")

            self.navigatedToUser = True

            return True

        except Exception as e:
            if self.verbose:
                log(self.verbose, f"An error occurred during search: {e}")
            return False

    def listReels(self) -> list[str]:
        '''Return the reel elements'''
        elements = []
        self.driver.get(self.instaBaseURL + config["targetUser"] + "/reels/")

        try:
            log(self.verbose, "Checking for the reelsPageButton.")
            WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, ProfilePage["reelsPageButton"]))
            )
            log(self.verbose, "Found reels page button")
        except NoSuchElementException as e:
            log(self.verbose, str(e))
            log(self.verbose, "No reels in this user's page.")

            return elements
    

        
        WebDriverWait(self.driver, self.standardWait).until(
            EC.presence_of_element_located((By.XPATH, ProfilePage["reelsParentContainer"]))
        )

        reelsContainer = self.driver.find_element(By.XPATH, ProfilePage["reelsParentContainer"])
        log(self.verbose, "Found reels parent container.")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while len(elements) <= config["maxNumberOfReelsToWatch"]:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            reels = reelsContainer.find_elements(By.TAG_NAME, "a")

            for reel in reels:
                href = reel.get_attribute("href")
                if not href in elements:    
                    elements.append(href)
    
            if new_height == last_height:
                break
            else:
                log(self.verbose, f"scrolled from {last_height} {new_height}")

            last_height = new_height

        elements = [e for e in elements if "https://www.instagram.com/reel/" in e]
        self.foundReels = elements[::]
        
        return elements

    def generateRandomComment(self):
        comment = "nice"

        try:
            with open(COMMENTS_FILE, "r") as f:
                comments = f.read().split("\n")
                comment = choice(comments)
        except Exception as e:
            log(self.verbose, str(e))
        return comment

    def generateRandomShareMessage(self):
        msg = "nice"

        try:
            with open(SHARE_MESSAGES_FILE, "r") as f:
                msg = f.read().split("\n")
                msg = choice(msg)
        except Exception as e:
            log(self.verbose, str(e))
        return msg

    def randomlyInteractWithReels(self):
        shuffle(self.foundReels)

        for customReelID in config["specificReelIDsToWatch"]:
            if not any([customReelID in link for link in self.foundReels]):
                self.foundReels.append(f"{self.instaBaseURL}reel/{customReelID}/")
                self.foundReels.pop(0)

        likeCount = randint(config["likeRangeMinimum"], config["likeRangeMinimum"])
        commentCount = randint(config["commentRangeMinimum"], config["commentRangeMinimum"])
        shareCount = randint(config["shareRangeMinimum"], config["shareRangeMaximum"])

        likeOrNot = [1 for _ in range(0, likeCount)] + [0 for _ in range(0, len(self.foundReels) - likeCount)]
        commentOrNot = [1 for _ in range(0, likeCount)] + [1 for _ in range(0, len(self.foundReels) - commentCount)]
        shareOrNot = [1 for _ in range(0, likeCount)] + [1 for _ in range(0, len(self.foundReels) - shareCount)]

        shuffle(likeOrNot)
        shuffle(commentOrNot)
        shuffle(shareOrNot)

        for i, reelLink in enumerate(self.foundReels):
            self.driver.get(reelLink)
            self.driver.implicitly_wait(config["realWatchDuration"])

            self.currentReelID = reelLink

            try:
                log(self.verbose, f"Waiting for reel {reelLink} to load")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, ReelPage["likeButton"]))
                )
                log(self.verbose, "Loaded.")
            except NoSuchElementException:
                log(self.verbose, f"Couldnt find like button for reel {reelLink}. Skipping")
                continue
            except TimeoutException:
                log(self.verbose, f"Couldnt load like button for reel {reelLink}. Timed out. Skipping")
                continue

            
            if config["like"] and likeOrNot[i] == 1:
                self.driver.implicitly_wait(config["individualInteractionInterval"])
                self.likeReel()
            
            if config["comment"] and commentOrNot[i] == 1:
                self.driver.implicitly_wait(config["individualInteractionInterval"])
                self.commentOnReel(self.generateRandomComment())

            if config["share"] and shareOrNot[i] == 1:
                self.driver.implicitly_wait(config["individualInteractionInterval"])
                self.shareReel(config["usersToShareTo"])
            
            self.driver.implicitly_wait(config["reelInteractionInterval"])

            


    def likeReel(self) -> bool:
        try:
            likeButton = self.driver.find_element(By.XPATH, ReelPage["likeButton"])
        except NoSuchElementException:
            log(self.verbose, "Couldn't find like button.")
            return False
        
        likeButton.click()
        log(self.verbose, f"Liked the reel  {self.currentReelID}")

        return True
    

    def commentOnReel(self, comment) -> bool:
        try:
            commentArea = self.driver.find_element(By.XPATH, ReelPage["commentArea"])
        except NoSuchElementException:
            log(self.verbose, "Couldn't find comment area.")
            return False
        
        
        commentArea.send_keys(comment)
        
        try: 
            commentButton = self.driver.find_element(By.XPATH, ReelPage["commentButton"])
        except NoSuchElementException:
            log(self.verbose, "Couldn't find comment button.")
            return False
        sleep(1)

        commentButton.click()
        log(self.verbose, f"Commented on reel {self.currentReelID}.")

        return True


    def shareReel(self, shareUsers):
        '''
        Procedure:
            1. Click share button.
            2. Type in the share to input box, the user name
            3. select the user.
            4. add share message.
            5. Click on the final share send.
        '''
        try:
            shareButton = self.driver.find_element(By.XPATH, ReelPage["shareButton"])
            shareButton.click()
        except NoSuchElementException:
            log("Did not get the share button.")
            return
        
        try:
            WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located(
                    (By.XPATH, ReelPage["shareToInput"])
                )
            )
            shareToInputBox = self.driver.find_element(By.XPATH, ReelPage["shareToInput"])

            for user in shareUsers:
                shareToInputBox.send_keys(user)

                try:
                    WebDriverWait(self.driver, self.standardWait).until(
                        EC.presence_of_element_located(
                            (By.XPATH, ReelPage["firstShareToResult"])
                        )
                    )

                    firstResult = self.driver.find_element(By.XPATH, ReelPage["firstShareToResult"])
                    firstResult.click()
                except TimeoutError:
                    log(f"User {user} did not load on the search suggestions box, skipping.")

                log(f"Sharing reel {self.currentReelID} to {user}")
            
            shareMessageInput =  self.driver.find_element(By.XPATH, ReelPage["shareMessageInput"])
            shareMessageInput.send_keys(self.generateRandomShareMessage())

            sendShareButton = self.driver.find_element(By.XPATH, ReelPage["sendShareButton"])
            sendShareButton.click()
            log(f"Shared reel {self.currentReelID}.")

        except TimeoutError:
            log("Share to input box did not load.")
        except NoSuchElementException as e:
            log(f"Something went wrong, did not find an element while sharing reels.: {str(e)}")


    def followUser(self, userName) -> bool:
        self.driver.get(f"{self.instaBaseURL}{userName}")

        try:
            log(self.verbose, f"Going to user page {userName}")
            
            WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, ProfilePage["followButton"]))
            )
            followButton = self.driver.find_element(By.XPATH, ProfilePage["followButton"])
            followButton.click()
            
            log(self.verbose, f"Followed user")

            return True
        except TimeoutException:
            log(self.verbose, "Already followed.")
            return False

    def exit(self):
        self.driver.quit()
        log(self.verbose, "Exited bot")

def getDriver(executablePath, firefoxPath, proxy = None, headless = False):
    s=Service(executable_path=executablePath)
    

    options = FirefoxOptions()
    options.add_argument('--disk-cache-dir=cache')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    
    
    if headless:
        options.add_argument("--headless=new")
    
    options.binary_location = firefoxPath
    
    if not proxy == None:
        # prox = Proxy()
        # prox.proxy_type = ProxyType.MANUAL
        # prox.http_proxy = proxy
        # prox.socks_proxy = proxy
        # prox.ssl_proxy = proxy
        # options.proxy = prox
        options.set_preference("network.proxy.type", 1)
        options.set_preference("network.proxy.http", proxy.split(":")[0])
        options.set_preference("network.proxy.http_port", proxy.split(":")[1])

    driver = webdriver.Firefox(service=s, options=options)
    return driver

def getFreeProxies():
    proxies = rq.get("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=ipport&format=text&country=in&timeout=1000").text.split("\r\n")

    proxies = [p for p in proxies if p != ""]
    
    return proxies

def installGeckoDriver():
    
    pass

def setup():
    if os.name == "nt":
        if not os.path.exists(FIREFOX_BINARY_LOCATION):
            print("You need to install firefox")
            exit()
        
        if not os.path.exists(GECKODRIVER_LOCATION):
            installGeckoDriver()


def getPing():
    ping = -1
    if os.name == "nt":
        data = check_output("ping www.instagram.com -n 10 ", shell=True).decode().split("\r\n")
        results = data[-2]
        # print(results)
        if "Average = " in results:
            avg = int(results[results.find("Average = ") + len("Average = "):-2]) * 2
            # print(avg)

            ping = avg
    return ping
    

def runBot(username, password, proxy = None):
    driver = getDriver(GECKODRIVER_LOCATION, FIREFOX_BINARY_LOCATION, proxy=proxy, headless=True)

    viewBot = ViewBot(username=username, password=password, driver = driver, config=config, verbose=True)
    
    viewBot.login()
    
    viewBot.searchAndNavigateToTargetUser()
    
    viewBot.listReels()
    
    viewBot.randomlyInteractWithReels()
    
    viewBot.followUser(config["targetUser"])
    
    viewBot.exit()

if __name__ == "__main__":
    config:Config = None
    with open("config.json", "r") as f:
        config:Config = json.load(f)

    
    proxies = config["proxies"]
    while len(proxies) == 0:
        try:
            proxies = getFreeProxies()
        except rq.exceptions.SSLError as e:
            log(True, f"The free proxies site is blocked on your network.\n{str(e)}")
            break
    proxiesInUse = []

    for i in range(1):
        for account in config["accounts"]:
            proxy = None
            if len(proxies) != 0 and config["useProxy"]:
                proxy = choice(proxies)
                proxiesInUse.append(proxy)

            log(True, f"Running bot with account {account['username']}")
            runBot(account["username"], account["password"], proxy)
        sleep(config["accountInteractionInterval"])

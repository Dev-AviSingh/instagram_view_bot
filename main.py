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
import configparser
from pprint import pprint
from ast import literal_eval

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
    proxy:str
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
CONFIGURATION_FILE = "config.ini"
PROXIES_FILE = "proxies.txt"
USERS_TO_SHARE_TO_FILE = "shareUsersList.txt"
ACCOUNT_CREDENTIALS_FILE = "accountLogins.txt"
# Proxies with this particular protocol
HTTP_PROXIES_FILE = "httpProxies.txt" 
SOCKS4_PROXIES_FILE = "socks4Proxies.txt"
SOCKS5_PROXIES_FILE = "socks5Proxies.txt" 

FIXED_PROXIES_FILE = "fixedProxies.json" # Accounts with their associated proxies fixed for them already.

GECKODRIVER_WINDOWS_LINK = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-win32.zip"
GECKODRIVER_LINUX_LINK = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz"

GECKODRIVER_LOCATION = "driver\\geckodriver.exe"
FIREFOX_BINARY_LOCATION = "firefox\\firefox.exe"



# If any of the configuration files do not exist. Create them.
localVariables = list(locals().items())
for var, val in localVariables:
    if "_FILE" in var:
        if os.path.exists(val):
            pass
        else:
            print(f"File does not exist: {val}")
            with open(val, "w") as f:
                pass


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
        self.config:Config = config

        if verbose:
            log(self.verbose, config)    

        self.instaBaseURL = "https://instagram.com/"

        self.standardWait += getPing() / 1000

        self.isLoggedIn = False
        self.navigatedToUser = False
        self.currentReelID = None

        log(self.verbose, f"Started bot for account {username} with password {password}.")
        driver.get(self.instaBaseURL)
    

    def login(self) -> bool:
        try:
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
            log(self.verbose, "Login successful")

            notNowButton = self.driver.find_element(By.XPATH, MainPage["saveLoginNotNowButton"])
            notNowButton.click()

            
            try:
                WebDriverWait(self.driver, self.standardWait).until(
                    EC.presence_of_element_located((By.XPATH, MainPage["notificationNotNowButton"]))
                )
            except NoSuchElementException:
                log(self.verbose, "Did not get notification message")
        
            log(self.verbose, "Login successful. Passed notifications alert.")

            notNowButton = self.driver.find_element(By.XPATH, MainPage["notificationNotNowButton"])
            notNowButton.click()
            

            self.isLoggedIn = True            
            return True

        except Exception as e:
            log(self.verbose, f"An error occurred during login: {e}")
            return False

    def searchAndNavigateToTargetUser(self) -> bool:
        try:
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
            search_bar.send_keys(self.config["targetUser"])
            search_bar.send_keys(Keys.RETURN)


            log(self.verbose, "Waiting for search results.")
            # Wait for search results to load
            WebDriverWait(self.driver, self.standardWait).until(
                EC.presence_of_element_located((By.XPATH, MainPage["searchedUsersContainer"]))
            )

            search_container = self.driver.find_element(By.XPATH, MainPage["searchedUsersContainer"])
            
            log(self.verbose, "Waiting for target's search result.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, MainPage["firstSearchResult"]))
            )
            
            log(self.verbose, "Going to user profile page")

            
            try:
                user_profile_search_result = search_container.find_element(By.XPATH, MainPage["firstSearchResult"])
                
                log(self.verbose, f"Search for '{self.config['targetUser']}' completed successfully")
                
                user_profile_search_result.click()
            except StaleElementReferenceException as e:
                log(self.verbose, "Stale element reference to first search result. Directly switching to reels page.")
                self.driver.get(f"{self.instaBaseURL}{self.config['targetUser']}")
            
            try:
                WebDriverWait(self.driver, self.standardWait).until(
                    EC.presence_of_element_located((By.XPATH, ProfilePage["username"]))
                )
            except NoSuchElementException as e:
                log(self.verbose, "Did not find username.")
            log(self.verbose, f"Navigated to target user {self.config['targetUser']} profile page.")

            self.navigatedToUser = True

            return True

        except Exception as e:
            log(self.verbose, f"An error occurred during search: {e}")
            return False

    def listReels(self) -> list[str]:
        '''Return the reel elements'''
        elements = []
        self.driver.get(self.instaBaseURL + self.config["targetUser"] + "/reels/")

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
        while len(elements) <= self.config["maxNumberOfReelsToWatch"]:
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

        for customReelID in self.config["specificReelIDsToWatch"]:
            if not any([customReelID in link for link in self.foundReels]):
                self.foundReels.append(f"{self.instaBaseURL}reel/{customReelID}/")
                self.foundReels.pop(0)

        likeCount = randint(self.config["likeRangeMinimum"], self.config["likeRangeMinimum"])
        commentCount = randint(self.config["commentRangeMinimum"], self.config["commentRangeMinimum"])
        shareCount = randint(self.config["shareRangeMinimum"], self.config["shareRangeMaximum"])

        likeOrNot = [1 for _ in range(0, likeCount)] + [0 for _ in range(0, len(self.foundReels) - likeCount)]
        commentOrNot = [1 for _ in range(0, likeCount)] + [1 for _ in range(0, len(self.foundReels) - commentCount)]
        shareOrNot = [1 for _ in range(0, likeCount)] + [1 for _ in range(0, len(self.foundReels) - shareCount)]

        shuffle(likeOrNot)
        shuffle(commentOrNot)
        shuffle(shareOrNot)

        for i, reelLink in enumerate(self.foundReels):
            self.driver.get(reelLink)
            self.driver.implicitly_wait(self.config["realWatchDuration"])

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

            
            if self.config["like"] and likeOrNot[i] == 1:
                self.driver.implicitly_wait(self.config["individualInteractionInterval"])
                self.likeReel()
            
            if self.config["comment"] and commentOrNot[i] == 1:
                self.driver.implicitly_wait(self.config["individualInteractionInterval"])
                self.commentOnReel(self.generateRandomComment())

            if self.config["share"] and shareOrNot[i] == 1:
                self.driver.implicitly_wait(self.config["individualInteractionInterval"])
                self.shareReel(self.config["usersToShareTo"])
            
            self.driver.implicitly_wait(self.config["reelInteractionInterval"])

            


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
    proxies = rq.get("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=ipport&format=text&country=in&timeout=1000&protocol=http").text.split("\r\n")

    proxies = [p for p in proxies if p != ""]
    
    return proxies


def getPing():
    ping = -1
    if os.name == "nt":
        data = check_output("ping www.instagram.com -n 10 ", shell=True).decode().split("\r\n")
        results = data[-2]
        
        if "Average = " in results:
            avg = int(results[results.find("Average = ") + len("Average = "):-2]) * 2
            ping = avg
        
    return ping

def testProxy(proxyUrl:str, port:int, protocol = "http", timeout = 2):
    proxies = {
        "http":f"{protocol}://{proxyUrl}:{port}"
    }
    try:
        r = rq.get(url="https://example.org", proxies=proxies, timeout=timeout)
    except rq.exceptions.ReadTimeout:
        return False
    except rq.exceptions.Timeout:
        return False
    except Exception as e:
        log(True, f"{protocol}://{proxyUrl}:{port} failed with exception\n{str(e)}.")
        return False
    
    if r.status_code == 200:
        return True
    else:
        return False


def fileToList(fileName) -> list[str]:
    data = []
    with open(fileName, "r") as f:
        data = f.read().split("\n")
        data = [p for p in data if p != "" and ":" in p]
    return data


def runBot(username, password, proxy = None, config = None):
    driver = getDriver(GECKODRIVER_LOCATION, FIREFOX_BINARY_LOCATION, proxy=proxy, headless=True)

    viewBot = ViewBot(username=username, password=password, driver = driver, config=config, verbose=True)
    
    viewBot.login()
    
    viewBot.searchAndNavigateToTargetUser()
    
    viewBot.listReels()
    
    viewBot.randomlyInteractWithReels()
    
    viewBot.followUser(config["targetUser"])
    
    viewBot.exit()

def loadConfiguration() -> Config:
    configuration:Config = {}

    log(True, "Loading config data")
    parser = configparser.ConfigParser()
    parser.read(CONFIGURATION_FILE)

    # print(parser.sections())
    # Reading configuration settings
    for section in parser.sections():
        keys = list(parser[section])
        for key in keys:
            val =  parser[section][key]
            if ',' in val:
                dataList = [v.strip() for v in val.split(",") if v != ""]
                configuration[key] = dataList
                continue
            try:
                configuration[key] = literal_eval(val.replace('true', "True").replace('false', 'False'))
            except ValueError:
                # print(val)
                configuration[key] = val

    with open(ACCOUNT_CREDENTIALS_FILE, "r") as f:
        data = f.read().split("\n\n")
        data = [d for d in data if d != "" and "username" in d]
        accounts = []

        for d in data:
            account = [l.strip().split("=")[1] for l in d.split("\n") if l != "" and "=" in l]
            accounts.append({
                "username":account[0],
                "password":account[1]
            })

        configuration["accounts"] = accounts
    log(True, "Loaded config data.")

    log(True, "Loading proxies")
    configuration["proxies"] = fileToList(PROXIES_FILE)
    configuration["usersToShareTo"] = fileToList(USERS_TO_SHARE_TO_FILE)
    httpProxies = map(lambda x: "http://" + x, fileToList(HTTP_PROXIES_FILE))
    socks4Proxies = map(lambda x: "socks4://" + x, fileToList(SOCKS4_PROXIES_FILE))
    socks5Proxies = map(lambda x: "socks5://" + x, fileToList(SOCKS5_PROXIES_FILE))
    
    configuration["proxies"].extend(httpProxies)
    configuration["proxies"].extend(socks4Proxies)
    configuration["proxies"].extend(socks5Proxies)

    configuration["proxies"] = list(set(configuration["proxies"]))

    proxyData = None
    with open(FIXED_PROXIES_FILE, "r") as f:
        proxyData = json.load(f)
    
    log(True, "Loaded proxies.")
    usedProxies = []
    unusedProxies = []
    badProxies = []

    log(True, "Testing proxies.")
    for proxy in configuration["proxies"]:
        protocol, ipport = proxy.split("://")
        ip, port = ipport.split(":")
        isActive = testProxy(ip, port, protocol)
        log(True, f"Testing proxy {proxy}")
        if isActive:
            if proxy in proxyData["usedProxies"]:
                usedProxies.append(proxy)
            else:
                unusedProxies.append(proxy)
        else:
            log(True, f"{proxy} is not working")
            badProxies.append(proxy)


    for account in configuration["accounts"]:
        # Update proxy statuses.
        if account["username"] in proxyData:
            # Account has a proxy associated to it.
            usedProxy = proxyData[account["username"]]

            if usedProxy in badProxies:
                usedProxies.remove(usedProxy)
                del proxyData[account["username"]]
                continue

            if not usedProxy in usedProxies:
                usedProxies.append(usedProxy)
            
            if usedProxy in unusedProxies:
                unusedProxies.remove(usedProxy)

        else:
            # Account does not have a proxy associated to it.
            if len(unusedProxies) != 0:
                newProxy = unusedProxies.pop()
                proxyData[account["username"]] = newProxy
            else:
                pass
    proxyData["usedProxies"] = usedProxies
    with open(FIXED_PROXIES_FILE, "w") as f:
        json.dump(proxyData, f)

    with open(PROXIES_FILE, "w") as f:
        f.write(
            "\n".join(configuration["proxies"])
        )

    for account in configuration["accounts"]:
        if account["username"] in proxyData:
            account["proxy"] = proxyData[account["username"]]
        else:
            account["proxy"] = ""
    configuration["proxyData"] = proxyData
    return configuration


if __name__ == "__main__":
    configuration:Config = None
    configuration = loadConfiguration()
    proxies = configuration["proxies"]
    pprint(configuration)

    runOnce = True
    log(True, "Started bot.")
    while True:
        for account in configuration["accounts"]:
            proxy = None
            if configuration["useProxy"] and "proxy" in account and account["proxy"] != "":
                proxy = account["proxy"]

            log(True, f"Running bot with account {account['username']}")
            runBot(account["username"], account["password"], proxy, config=configuration)
        
        if runOnce:
            break
        
        sleep(configuration["accountInteractionInterval"])

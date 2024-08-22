ProfilePage:dict[str, str] = {
    "username":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[2]/div/div/div[1]/div/a/h2/span",
    "followButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[2]/div/div/div[2]/div/div/button",
    "reelsParentContainer":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main",
    "reelsPageButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[1]/a[2]"
}

ReelPage:dict[str, str] = {
    "likeButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/div/div[2]/div/div[3]/section[1]/div[1]/span[1]/div/div/div",
    "commentArea":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/div/div[2]/div/div[4]/section/div/form/div/textarea",
    "commentButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/div/div[2]/div/div[4]/section/div/form/div/div[2]/div",
    "shareButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[3]/section[1]/div[1]/button",
    "shareToInput":"/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[1]/div/div[2]/input",
    "firstShareToResult":"/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/div[1]",
    "shareMessageInput":"/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[2]/div[1]/div/input",
    "sendShareButton":"/html/body/div[9]/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div"
}

MainPage:dict[str, str] = {
    "username":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div[1]/div[2]/div/div[1]/div/div/div/div/div/div[2]/div/div/div/a",
    "searchButton":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[2]/span/div/a/div/div[2]/div/div/span/span",
    "searchBar":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div[2]/div/div/div[1]/div/div/input",
    "searchedUsersContainer":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div[2]/div/div/div[2]/div",
    "saveLoginNotNowButton":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/div/div/div",
    "notificationNotNowButton":"/html/body/div[2]/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]",
    "suspectedBehaviour":"/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[2]/div/div/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div/span",
    "firstSearchResult":"/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div[2]/div/div/div[2]/div/a[1]"
}

import mariadb
from random import randint, choice

connection = mariadb.connect(
    host = "127.0.0.1",
    port = 6969,
    user = "root",
    password = "password",
    database = "studentinfo"
)
names = ("Avi", "ravi", "shyam", "ghanshyam", "raju", "saraswati", "ram")
surnames = ("singh", "bhangale", "teli", "pandit", "koranne", "nelekar", "tukaram")
cities = ("pune", "bombay", "ncr", "delhi", "ghaziabad", "gurgaon")
with connection.cursor() as c:
    for rollno in range(10000):
        name = f"{choice(names)} {choice(surnames)}"
        statement = f'''INSERT INTO si VALUES ({rollno}, "{name}", "{choice(cities)}", {randint(20, 30)}, {randint(50, 100)})'''
        # print(statement)
        c.execute(statement)
    connection.commit()
connection.close()
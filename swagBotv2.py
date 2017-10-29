from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import unittest
from operator import itemgetter
from random import shuffle
from selenium.common.exceptions import NoSuchElementException
import time

#dict of all categories with correspondingly link, sorted in sb min to max
sites = {'news':'http://www.swagbucks.com/watch/playlists/333/news-politics?sort=1',
            'editors':'http://www.swagbucks.com/watch/playlists/111/editors-pick?sort=1',
            'film':'http://www.swagbucks.com/watch/playlists/133/entertainment?sort=1',
            'food':'http://www.swagbucks.com/watch/playlists/3/food?sort=1',
            'health':'http://www.swagbucks.com/watch/playlists/4/health?sort=1',
            'careers':'http://www.swagbucks.com/watch/playlists/1/careers?sort=1',
            'fashion':'http://www.swagbucks.com/watch/playlists/98/fashion?sort=1',
            'fitness':'http://www.swagbucks.com/watch/playlists/101/fitness?sort=1',
            'hobbies':'http://www.swagbucks.com/watch/playlists/650/hobbies?sort=1',
            'homeimprovement':'http://www.swagbucks.com/watch/playlists/12/home-garden?sort=1',
            'music':'http://www.swagbucks.com/watch/playlists/447/music?sort=1',
            'parenting':'http://www.swagbucks.com/watch/playlists/138/parenting?sort=1',
            'finance':'http://www.swagbucks.com/watch/playlists/1999/personal-finance?sort=1',
            'animals':'http://www.swagbucks.com/watch/playlists/91/pets-animals?sort=1',
            'shopping': 'http://www.swagbucks.com/watch/playlists/692/shopping?sort=1',
            'sports' : 'http://www.swagbucks.com/watch/playlists/17/sports?sort=1',
            'tech' : 'http://www.swagbucks.com/watch/playlists/22/technology?sort=1',
            'travel' : 'http://www.swagbucks.com/watch/playlists/129/travel?sort=1',
            'wedding': 'http://www.swagbucks.com/watch/playlists/120/wedding?sort=1'
              }

#list of categories for indexing
categories = sites.keys()
shuffle(categories)
watchedPlaylists = []


class VideoAlreadyWatched(Exception): pass

class LoginTest(unittest.TestCase):

    def setUp(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--mute-audio") #mute chrome audio

        self.driver = webdriver.Chrome('/Users/willmati/Desktop/chromedriver',chrome_options=chrome_options)
        self.driver.get("https://www.swagbucks.com/p/login")

    def establishConnection(self):
        driver = self.driver
        WebDriverWait(driver, 1000).until(lambda driver: driver.current_url == 'http://www.swagbucks.com/watch')
        print 'At destination'

    def connectToCategory(self, website):
        driver = self.driver
        self.driver.get(website)

    def finalizeCardInfo(self, L):
        RefinedList = L[:] #duplicate list
        self.cleanList(RefinedList) #calc SB/min rate
        return RefinedList

#get list that gathers category playlists & info
    def getCardInfo(self):
        source = self.driver.page_source
        Soup = BeautifulSoup(source, 'html.parser')
        L = []
        for child in  Soup.find('div', {'id':'cardDeck'}).children:
            L.append([child.find('h1').get_text().encode('utf-8').strip(), #playlist name
                      child.find('p', {'class':'sbTrayListItemTimeContainer'}).get_text().encode('utf-8').strip(), #playlist duration
                      child.find('span', {'class':'sbTrayListItemSbEarn sbColor1'}).find('span').get_text()[0].encode('utf-8').strip(), #SB
                      None]) #playlist name, URL, SB, Duration(mins), SB/min
        return self.organizeList(self.finalizeCardInfo(L))

#organize the list by sb/min with most profitable playlists at the start of the list
    def organizeList(self, L):
        return sorted(L, key=itemgetter(3), reverse=True)

#click on the card/element of the playlist to open it fromc category page
    # def clickCard(self, playlistTitle):
    #     driver = self.driver
    #     cardpath = "//h1[contains(text(),'" + playlistTitle + "')]"
    #     cardpathElement = WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(cardpath))
    #     cardpathElement.click()

    def getCardID(self, pListTitle):
            source = self.driver.page_source
            Soup = BeautifulSoup(source, 'html.parser')
            pListIDNum = Soup.find('h1', text=pListTitle, attrs={'class':'sbTrayListItemHeaderCaption cardHeader withEllipsis watchHeader truncated'}).get('id').encode('utf-8').strip()[-10:]
            pListID = 'sbHomeCard' + pListIDNum
            return pListID

    def clickCard(self, playlistTitle):
        driver = self.driver
        pListID = self.getCardID(playlistTitle)
        CardElement = WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_id(pListID))
        CardElement.click()


#if playlist is finished watching, return to category page
    def returnToPage(self, site):
        driver = self.driver
        watchedPath = '//*[@id="watchVideosEarn"]'
        WebDriverWait(driver, 2500).until(EC.text_to_be_present_in_element((By.XPATH, watchedPath), 'Watched'))
        print 'Watched All Videos in Playlist'
        driver.get(site)

#after playlist is finished watching, add title to watchedlist
    def updateWatchedList(self, pListTitle):
        if pListTitle not in watchedPlaylists:
            watchedPlaylists.append(pListTitle)
            print watchedPlaylists

#tests to see if playlist is watched. test 1) scan through watched list test 2)look at playlist card/element and see scan if it has been watched
    def checkIfWatched(self, pListTitle):
        source = self.driver.page_source
        Soup = BeautifulSoup(source, 'html.parser')
        pListID = self.getCardID(pListTitle)
        plistWatchTag = Soup.find('section', id=pListID).find('div', class_='playlistWasWatched')

        if pListTitle in watchedPlaylists:
            raise VideoAlreadyWatched
        elif plistWatchTag != None:
            raise VideoAlreadyWatched
        else:
            pass

#function to run through playlists, and watch videos
    def cycleCards(self, pListData, pListSite):

            for pList in pListData:
                try:
                    self.checkIfWatched(pList[0])
                    self.clickCard(pList[0])
                    self.switchVideos()
                    self.returnToPage(pListSite)
                    self.updateWatchedList(pList[0])
                except VideoAlreadyWatched:
                    continue
#format playlist data list
    def cleanList(self, list):
        for playlist in list:
            # elimate playlists over an hour
            if 'h' in playlist[1]:
                list.pop(list.index(playlist))
                break
            # format duration for mathematical operation and add SB/min rate
            if 'm' in playlist[1][1]:
                playlist[3] = round((float(playlist[2]) / float(playlist[1][0])), 3)
            else:
                playlist[3] = round((float(playlist[2]) / float(playlist[1][0:2])), 3)

            if playlist[3] < 0.07:
                list.pop(list.index(playlist))
                break
#main function that runs everything
    def test_watchPlaylist(self):
        driver = self.driver
        self.establishConnection()
        for i in range(len(categories)):
            website = sites[categories[i]]
            driver.get(website)
            playlistInfo = self.getCardInfo()
            print 'Data Structure Established'
            self.cycleCards(playlistInfo, website)
            continue

#manually switch videos as soon as current video is finished watching
    def switchVideos(self):
        while 1:
            try:
                if self.VideoWatched():
                        self.nextVideo()
            except NoSuchElementException:
                break

#test to see if a video has been watched yet
    def VideoWatched(self):
        source = self.driver.page_source
        Soup = BeautifulSoup(source, 'html.parser')
        currentVideoSymbol = Soup.find("p", class_="nowPlayingText").previous_element.find_previous_sibling("div", class_="sbPlaylistVideoNumber")
        for elem in currentVideoSymbol.find_all(class_=True):
            if str(elem.get('class')) == "[u'iconWatch', u'iconCheckmark']":
                return True
            else:
                return False

    def nextVideoXpath(self):
        source = self.driver.page_source
        Soup = BeautifulSoup(source, 'html.parser')
        currentTitle = str(Soup.find('span', class_='unbold').get_text().encode('utf-8').strip())
        nextVidPath = '''//*[@title="''' + currentTitle + '"]/following-sibling::a'
        print nextVidPath
        print currentTitle
        return nextVidPath

#select and click next video
    def nextVideo(self):
        driver=self.driver
        try:
            nextVidElement = driver.find_element_by_xpath(self.nextVideoXpath())
            if nextVidElement == None:
                raise NoSuchElementException
            else:
                nextVidElement.click()
        except AttributeError:
            return None





if __name__ == '__main__':
    unittest.main()
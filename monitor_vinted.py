import requests
import json
from time import sleep
from discord_webhook import DiscordEmbed, DiscordWebhook
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from pandas._libs.missing import NAType
from random import randint

# Creating a pool of random user-agent
software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value] 
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

class MonitorVinted:

    def __init__(self, keyword : str, filter : str, rpp : str, price_min : str, price_max : str, seller_min_eval : str, seller_min_mark : str , proxies : str, webhook_link : str, delay : int, webhook_avatar : str, webhook_name : str) -> None:
        self.keyword = keyword
        if type(filter) is NAType: # Excepting csv blank values
            self.filter = ""
        else:
            self.filter = filter
        self.rpp = rpp
        if type(price_min) is NAType:
            self.price_min = None
        else: 
            self.price_min = price_min
        if type(price_max) is NAType:
            self.price_max = None
        else: 
            self.price_max = price_max
        if type(seller_min_eval) is NAType:
            self.seller_min_eval = None
        else: 
            self.seller_min_eval = int(seller_min_eval)
        if type(seller_min_mark) is NAType:
            self.seller_min_mark = None
        else: 
            self.seller_min_mark = float(seller_min_mark)
        if type(proxies) is NAType:
            self.proxies = None
        else:
            self.proxies = []
            with open(f"proxies\\{proxies}.txt", "r", encoding="utf-8") as proxy_file:
                for line in proxy_file:
                    proxy_elements = line.split(":")
                    proxy = proxy_elements[2] + ":" + proxy_elements[3] + "@" + proxy_elements[0] + ":" + proxy_elements[1]
                    self.proxies.append({"http": "http://" + proxy, "https": "htTps://" + proxy})
        self.webhook_link = webhook_link
        self.webhook_avatar = webhook_avatar
        self.webhook_name = webhook_name
        self.delay = delay
        self._pairs_already_pinged = [{}]

    @property
    def self_pairs_already_pinged(self):
        return self._pairs_already_pinged

    @self_pairs_already_pinged.setter
    def pairs_already_pinged(self, infos : dict):
        if len(self._pairs_already_pinged) < 100:
            self._pairs_already_pinged.append(infos)
        else:
            self._pairs_already_pinged = [infos]

    def __send_webhook(self, dict_shoe : dict):
        embed = DiscordEmbed(title=dict_shoe["title"], color="a0a0a0")
        embed.set_timestamp()
        embed.set_thumbnail(url=dict_shoe["image"])
        embed.add_embed_field(name="Price", value=f'{dict_shoe["price"]}')
        embed.add_embed_field(name="Size", value=f'{dict_shoe["size"]}')
        embed.set_url(dict_shoe["link"])
        embed.set_footer(text=self.webhook_name, icon_url=self.webhook_avatar)
        webhook = DiscordWebhook(url=self.webhook_link, username=self.webhook_name, avatar_url=self.webhook_avatar)
        webhook.add_embed(embed)
        try:
            resp = webhook.execute(remove_embeds=True, remove_files=True)
            if resp.ok:
                return True, None
            else:
                return False, resp
        except Exception as e:
            print(f'Error sending webhook ! {e}')
            return False, None

    def __userReputation(self, user_id : int, session : requests.Session, user_agent : dict, proxy : dict) -> bool:
        get = session.get(f"https://www.vinted.fr/api/v2/users/{str(user_id)}?localize=false", headers=user_agent, proxies=proxy)
        if get.ok:
            json_resp = json.loads(get.text)
            if (self.seller_min_eval != None) and (self.seller_min_mark):
                if (json_resp["user"]["positive_feedback_count"] + json_resp["user"]["positive_feedback_count"] + json_resp["user"]["positive_feedback_count"] >= self.seller_min_eval) and (json_resp["user"]["feedback_reputation"] >= self.seller_min_mark):
                    return True
            elif (self.seller_min_eval != None):
                if json_resp["user"]["positive_feedback_count"] + json_resp["user"]["positive_feedback_count"] + json_resp["user"]["positive_feedback_count"] >= self.seller_min_eval:
                    return True
            else:
                if json_resp["user"]["feedback_reputation"] >= self.seller_min_mark:
                    return True
        else:
            return False

    def __getProducts(self) -> list:
        list_products = []
        try:
            proxy = None
            if self.proxies != None:
                proxy = self.proxies[randint(0, len(self.proxies) - 1)]
            user_agent = {"user-agent": user_agent_rotator.get_random_user_agent()} 
            with requests.Session() as s:
                fetch = s.get("https://www.vinted.fr/", headers=user_agent, proxies=proxy)
                if fetch.ok:
                    params_search = {
                        "search_text": self.keyword.replace(" ", "+"),
                        "is_for_swap": "0",
                        "page": "1",
                        "per_page": self.rpp,
                        "order": "newest_first"     
                    }
                    if self.price_min != None:
                        params_search["price_from"] = self.price_min
                        params_search["currency"] = "EUR"
                    if self.price_max != None:
                        params_search["price_to"] = self.price_max
                        params_search["currency"] = "EUR" 

                    search = s.get("https://www.vinted.fr/api/v2/catalog/items", params=params_search, headers=user_agent, proxies=proxy)
                    if search.ok:
                        json_resp = json.loads(search.text)
                        for item in json_resp["items"]:
                            if (self.seller_min_mark != None) or (self.seller_min_mark != None) and (self.filter in item["title"]):
                                if self.__userReputation(item["user"]["id"], s, user_agent, proxy):
                                    list_products.append({
                                        "title": item["title"],
                                        "link": item["url"],
                                        "price": str(item["price"]) + "€",
                                        "image": item["photo"]["url"],
                                        "size": item["size_title"]
                                    })
                            elif self.filter in item["title"]:
                                list_products.append({
                                        "title": item["title"],
                                        "link": item["url"],
                                        "price": str(item["price"]) + "€",
                                        "image": item["photo"]["url"],
                                        "size": item["size_title"]
                                    })
                else:
                    print("Error fetching Vinted" + str(fetch))
        except Exception as e:
            print(f"Unexpected error : {e}")
        finally:
            return list_products

    def monitor(self) -> None:
        try:
            while True:
                products = self.__getProducts()
                for product in products:
                    if product not in self._pairs_already_pinged:
                        isSent, err = self._MonitorVinted__send_webhook(product)
                        if not isSent and err != None:
                            print(err)
                        elif not isSent and err == None:
                            pass
                        else:
                            self.pairs_already_pinged = product
        except Exception as e:
            print(f"Error monitoring : {e}")
        finally:
            sleep(self.delay)

'''
input
extractSymbols(input)(separate function)->symbols
interpretations = []
for symbol in symbols
    interpretation.append(extractSymbolInterpretation(symbol) (separate function))
summarize (separate function)
'''
from uuid import uuid4
from inMemoryStore import SingletonJobsKv, SymbolLink, SymbolInterpretation
import os
from groq import Groq
import re
import json
import requests
import bs4
from singletonGroq import SingleGroq

class SymbolInterpreter:
    def __init__(self):
        self.kvInstance = SingletonJobsKv.getInstance()
        # self.groqClient = Groq(
        # api_key=os.environ.get("GROQ_API_KEY"),
        # )
        self.groqClient = SingleGroq.getInstance()
        self.serperHeaders = {
        'X-API-KEY': 'a88471bb323dabc70364da234a1f0f6cdec01aac',
        'Content-Type': 'application/json'
        }
        self.serperUrl = "https://google.serper.dev/search"
        self.result = []

    def extractListFromText(self, text):
        list_pattern = re.compile(r'\[([^\[\]]+)\]')
        match = list_pattern.search(text)
        try:
            if match:
                # Extracting the list
                extracted_list = match.group(1)
                # Splitting the string to get individual items
                items = extracted_list.split(',')
                # Stripping extra spaces and quotes from each item
                items = [item.strip(' " ') for item in items]
                if len(items)>2:
                    items = items[:2]
                return items
            else:
                print("No list found in the string.")
                return []
        except Exception as e:
            return []

    def extractSymbols(self):
        try:
            obj = {
                "role": "user",
                "content": f'''{self.rawDream} extract the relevant google search prompts based on different jungian symbols occuring in the dream above for jungian dream analysis and return an array list containing the search prompts, in the following
                output format: ["search prompt 1", "search prompt 2", "search prompt 3"],  IMPORTANT: each search must contribute to jungian analysis of the dream, make sure to only respond with a single array containing searche prompts in the given format, also make sure each prompt in the output array must be sorted based on jungian relevance, also include different searche prompts which dont have much overlap in meaning with each other''',
            }
            chat_completion = self.groqClient.chat.completions.create(
                messages=[obj],
                model="llama-3.3-70b-versatile",
            )
            with self.kvInstance.getLock():
                event = self.kvInstance.appendCosting(self.jobId, {"category":"groqApi", "cost":0, "calls":1, "groqUsage":chat_completion.usage.model_dump_json()})
                self.kvInstance.appendEvent(self.jobId, str(event))
            text=chat_completion.choices[0].message.content
            return text
        except Exception as e:
            print(str(e))
            return "error occured"

    def extractSymbolLink(self, symbol):
        payload = json.dumps({
        "q": f'''{symbol}'''
        })
        response = requests.request("POST", self.serperUrl, headers=self.serperHeaders, data=payload)
        with self.kvInstance.getLock():
            event = self.kvInstance.appendCosting(self.jobId,{"category":"serperApi", "cost":83/1000, "calls":1})
            self.kvInstance.appendEvent(self.jobId, str(event))
        link = ""
        data = response.json()
        try:
            if 'organic' in data:
                arr = data['organic']
                if len(arr)>0:
                    link = arr[0]['link']
                    title = arr[0]['title']
                    return SymbolLink(symbol, link, title)
        except Exception as e:
            print(e)
            return {"status":"error"}
        return {"status":"linkNotFound"}

    def paraphraseInterpretation(self, rawInterpretation, symbol):

        try:
            obj={
                        "role": "user",
                        "content": f'''{rawInterpretation}  Symbol: {symbol} Task: retrieve all the relevant info and use direct quotations for relating the given interpretation above with the following dream, {self.rawDream}    IMPORTANT: ONLY USE THE INTERPRETATION PROVIDED ABOVE TO INTERPRET THE DREAM IN A JUNGIAN STYLE AND NOTHING ELSE, MAKE SURE TO USE DIRECT QUOTATIONS BY JUNG GIVEN IN THE INTERPRETATION''',
                    }
            chat_completion = self.groqClient.chat.completions.create(
                messages=[obj],
                model="llama-3.3-70b-versatile",
            )
            with self.kvInstance.getLock():
                event = self.kvInstance.appendCosting(self.jobId,{"category":"groqApi", "cost":0, "calls":1, "groqUsage":chat_completion.usage.model_dump_json()})
                self.kvInstance.appendEvent(self.jobId, str(event))
            return chat_completion.choices[0].message.content
        except Exception as e:
            return ""

    def scrapeSymbolInterpretation(self, link):
        try:
            response = requests.get(link,headers={'User-Agent': 'Mozilla/5.0'})
            soup = bs4.BeautifulSoup(response.text,'lxml')
            allText = soup.body.get_text(' ', strip=True)
            return allText
        except:
            return ""

    def summarize(self):
        # Implement the logic to summarize interpretations
        pass

    def interpret(self, jobId, dream):
        try:
            self.rawDream = dream
            self.jobId = jobId
            print("jobid", self.jobId)
            with self.kvInstance.getLock():
                self.kvInstance.appendEvent(self.jobId,"STARTED")
            print("starteddddd")
            symbolText = self.extractSymbols()
            print("symbolTextExtracted", symbolText)
            symbolList = self.extractListFromText(symbolText)
            print("symbolListExtracted", symbolList)
            if len(symbolList)==0:
                with self.kvInstance.getLock():
                    self.kvInstance.appendEvent(self.jobId,"retryingSymbolExtraction")
                symbolText = self.extractSymbols()
                symbolList = self.extractListFromText(symbolText)
            with self.kvInstance.getLock():
                event = self.kvInstance.updateJobSymbols(self.jobId, symbolList)
                self.kvInstance.appendEvent(self.jobId,str(event))
            for symbol in symbolList:
                print(symbol)
                symbolLinkObj = self.extractSymbolLink(symbol)
                with self.kvInstance.getLock():
                    event = self.kvInstance.appendSymbolLink(self.jobId, symbolLinkObj)
                    self.kvInstance.appendEvent(self.jobId, event)
                scrapedData = self.scrapeSymbolInterpretation(symbolLinkObj.link)
                print("datascraped")
                interpretation = self.paraphraseInterpretation(scrapedData, symbol)
                print("interpreted")
                self.result.append(SymbolInterpretation(symbol, interpretation))
                with self.kvInstance.getLock():
                    event = self.kvInstance.appendSymbolInterpretation(self.jobId, SymbolInterpretation(symbol, interpretation))
                    self.kvInstance.appendEvent(self.jobId, str(event))
            with self.kvInstance.getLock():
                self.kvInstance.updateJobStatus(self.jobId, "COMPLETED")
            self.kvInstance.appendEvent(self.jobId, "COMPLETED")
            with self.kvInstance.getLock():
                job = self.kvInstance.getJob(self.jobId)
            return job
        except Exception as e:
            self.kvInstance.appendEvent(self.jobId, "ERROR")
            return


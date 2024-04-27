from crewai import Agent, Task
from textwrap import dedent
from models import DreamSymbolList, SymbolsUrls, FinalDreamOutput
from typing import List
from inMemoryStore import SingletonInMemoryEvents

class DreamAnalysisTasks:
    def __init__(self, jobId:str):
        self.jobId = jobId

    def appendEventCallback(self, taskOutput):
        inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
        inMemoryStore.appendEvent(self.jobId, taskOutput.exported_output)

    def appendEventCallbackRaw(self, taskOutput):
        inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
        if len(str(taskOutput.exported_output))>50:
            eventOutput = str(taskOutput.exported_output)
            eventOutput = eventOutput[:50]+'.....'

        inMemoryStore.appendEvent(self.jobId, eventOutput)
        inMemoryStore.updateRawAnalysis(self.jobId, taskOutput.exported_output)

    def symbolExtraction(self, agent: Agent, dream:str):
        return Task(
            description=dedent(f"""Based on the dream: {dream},
                use the jungian symbols to form the final output dont use the meaning of the symbols.
                """),
            agent=agent,
            expected_output=dedent(
                """A json object containing the list of 3 most symbols in the key symbols"""),
            output_json=DreamSymbolList,
            callback=self.appendEventCallback
        )

    def getWebUrlsOg(self, agent:Agent, tasks:List[Task]):
        return Task(
            description=dedent(f"""Based on the list of symbols returned from the symbol Extractor Agent, research each symbol put together a json object containing the URLs for at most 5 of the most relevant jungaian symbols
                """),
            agent=agent,
            expected_output=dedent(
                """A json object containing the url for each symbol in the format {"data":{"symbol1":"link1", "symbol2":"link2",...}}"""),
            output_json=SymbolsUrls,
            context=tasks,
            callback=self.appendEventCallback
        )

    def getWebData(self, agent:Agent, tasks:List[Task]):
        return Task(
            description=dedent(f"""Based on the list of symbols returned from the symbol Extractor Agent, research each symbol on the web using the given tool and generate an extensive jungian text analysis consisting of references to the symbols.The final article must contain direct quotations by jung and also book references if any. The report has to have extensive text with heavy jungian meanings of symbols fetched from the web. article should contain all the relevant information scraped from the web.
            make sure to be careful about the input format of the given serper web scraping api tool
            Only use the data you scraped from the internet to interpret the symbols
            you MUST break the execution in case the serper google api fails to scrape the data and return an empty string"""),
            agent=agent,
            context=tasks,
            callback=self.appendEventCallbackRaw,
            expected_output=dedent(
                """A huge string containing the meaning for each symbol in paragraphs and also some reference books relevant to the scraped data"""),
            )

    def shortSummaryTask(self, agent:Agent, tasks:List[Task]):
        return Task(
            description=dedent(f"""Based on the dream analysis received from the relevantSymbolMeaningAgent agent write a short, profound and perspective shifting summary of the dream analysis.
            it should have also have some suggestions as to the things the dreamer can focus on based on the dream analysis.
            Only use the data you received from the getWebData Task by relevantSymbolMeaningAgent agent"""),
            agent=agent,
            context=tasks,
            callback=self.appendEventCallback,
            expected_output=dedent(
                """A string containing the profound summary of the long dream analysis received by the previous agent"""),
            )


    def writerAgentTask(self, agent:Agent, tasks:List[Task], dream:str):
        return Task(
        description=dedent(f"""Write an extensive and deep jungian analysis with text only and at least 10 paragraphs. text should make heavy use of
        the scraped data retrieved by the relevantSymbolMeaningAgent. Style and tone should be very jungian, philosphical, quirky and relevant to psychology
        Don't write "**Paragraph [number of the paragraph]:**", instead start the new paragraph in a new line.
        ALWAYS include links to symbol meanings which you find while scraping.
        """),
        agent=agent,
        context=tasks,
        callback=self.appendEventCallback,
        expected_output=dedent(
                """A string containing the full analysis of the dream based on the relevant Jungian symbols present in the dream"""),
        )
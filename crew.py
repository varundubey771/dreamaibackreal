from crewai import Crew, Process
from agents import DreamAnalysisAgents
from tasks import DreamAnalysisTasks
from inMemoryStore import SingletonInMemoryEvents
class DreamAnalysisCrew:
    def __init__(self, jobId, model='groq'):
        print("mdomodemodemodemodmeodmeomdoedmomdoel", model)
        self.jobId = jobId
        self.crew = None
        self.model=model

    def setup_crew(self, dream):
        agents =  DreamAnalysisAgents(self.model)
        tasks = DreamAnalysisTasks(self.jobId)
        symbolsAgent = agents.symbolExtarctorAgent(dream)
        symbolExtractionTask = tasks.symbolExtraction(symbolsAgent, dream)
        meaningAgent = agents.relevantSymbolMeaningAgent()
        meaningExtractionTask = tasks.getWebData(meaningAgent, [symbolExtractionTask])
        # summmaryAgent = agents.summaryAgent()
        # summaryTask = tasks.shortSummaryTask(summmaryAgent, [meaningExtractionTask])
        try:
            self.crew = Crew(agents=[symbolsAgent, meaningAgent], tasks=[symbolExtractionTask, meaningExtractionTask] ,process=Process.sequential)
        except Exception as e:
            print("errr", e)

    def kickoff(self):
        inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
        if not self.crew:
            return {"status":"no_crew_present"}
        inMemoryStore.appendEvent(self.jobId, "crew started")
        try:
            res=self.crew.kickoff()
            print("ressssssssssssssKickOff", res)
            return res
        except Exception as e:
            return str(e)




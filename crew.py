from crewai import Crew, Process
from agents import DreamAnalysisAgents
from tasks import DreamAnalysisTasks
class DreamAnalysisCrew:
    def __init__(self):
        self.crew = None

    def setup_crew(self, dream):
        agents =  DreamAnalysisAgents()
        tasks = DreamAnalysisTasks()
        symbolsAgent = agents.symbolExtarctorAgent(dream)
        symbolExtractionTask = tasks.symbolExtraction(symbolsAgent, dream)
        webAgent = agents.relevantSymbolMeaningAgent()
        webDataTask = tasks.getWebData(webAgent, [symbolExtractionTask])
        writerAgent = agents.finalWriter()
        writerTask = tasks.writerAgentTask(writerAgent, [webDataTask], dream)
        try:
            self.crew = Crew(agents=[symbolsAgent, webAgent], tasks=[symbolExtractionTask, webDataTask] ,process=Process.sequential)
        except Exception as e:
            print("errr", e)

    def kickoff(self):
        if not self.crew:
            return {"status":"no_crew_present"}
        try:
            res=self.crew.kickoff()
            print("ressssssssssssssKickOff", res)
            return res
        except Exception as e:
            return str(e)




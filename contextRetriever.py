from singletonGroq import SingleGroq

class ContextRetriever:
    def __init__(self, dream:str):
        self.groqClient  = SingleGroq.getInstance()
        self.dream = dream

    def getRelevantQuestions(self):
        try:
            obj = {
                "role": "user",
                "content": f'''{self.dream} ask the dreamer concise, personal and relevant jungian questions to retrieve more context for the dream. ask questions which might be useful to extract relevant context for jungian analysis of the dream, only ask 3 to 4 questions''',
            }
            chat_completion = self.groqClient.chat.completions.create(
                messages=[obj],
                model="llama-3.3-70b-versatile",
            )
            # with self.kvInstance.getLock():
            #     event = self.kvInstance.appendCosting(self.jobId, {"category":"groqApi", "cost":0, "calls":1, "groqUsage":chat_completion.usage.model_dump_json()})
            #     self.kvInstance.appendEvent(self.jobId, str(event))
            text=chat_completion.choices[0].message.content
            return text
        except Exception as e:
            print(str(e))
            return "error occured"
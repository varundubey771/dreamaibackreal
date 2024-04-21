from flask import Flask, request
from groq import Groq
import os
from crew import DreamAnalysisCrew

app = Flask('dream_agent')


def kickoffCrew(dream:str):
    results = None
    try:
        dreamAnalysisCrew = DreamAnalysisCrew()
        dreamAnalysisCrew.setup_crew(dream)
        results = dreamAnalysisCrew.kickoff()
    except Exception as e:
        print("err", e)
    return results


@app.route('/groqdream', methods=['POST'])
def groqDream():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    res = kickoffCrew(data['dreamWithContext'])
    print("@@@@@@@@@@@@@@@@@@@", res)
    return res


@app.route('/getDreamWithContext', methods=['POST'])
def getDream():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    obj =             {
                "role": "user",
                "content": f'''only extract the jungian symbols and dont do anything else from the following dream: {data['dreamWithContext']}''',
            }
    chat_completion = client.chat.completions.create(
        messages=[
obj
        ],
        model="mixtral-8x7b-32768",
    )
    print(obj)
    return {"analysis":chat_completion.choices[0].message.content}

app.run(debug=True)

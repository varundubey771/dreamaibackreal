from flask import Flask, abort, request, jsonify
from groq import Groq
import os
from crew import DreamAnalysisCrew
from threading import Thread
from uuid import uuid4
from inMemoryStore import SingletonInMemoryEvents, Event, SingletonJobsKv, SymbolLink
from flask_cors import CORS, cross_origin
from db import SingleDb
from functools import wraps
import re
import bs4, requests
import json
from symbolInterpreter import SymbolInterpreter



app = Flask('dreamAgent')
CORS(app)
def kickoffCrew(jobId:str, dream:str):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    res = None
    try:
        dreamAnalysisCrew = DreamAnalysisCrew(jobId)
        dreamAnalysisCrew.setup_crew(dream)
        res = dreamAnalysisCrew.kickoff()
    except Exception as e:
        inMemoryStore.appendEvent(jobId, 'event crew kickoff failed')
        inMemoryStore.updateJobStatus(jobId, 'ERROR')
        inMemoryStore.updateJobAnalysisSummary(jobId, str(e))
        print(str(e))
        return {"status":"failed"}
    print("@#################################", res, type(res))
    inMemoryStore.updateJobStatus(jobId, 'COMPLETE')
    inMemoryStore.updateJobAnalysisSummary(jobId, res)
    inMemoryStore.appendEvent(jobId, 'COMPLETE')
    print(jobId)

def kickoffCrewPremium(jobId:str, dream:str):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    res = None
    try:
        dreamAnalysisCrew = DreamAnalysisCrew(jobId, 'chatgpt')
        dreamAnalysisCrew.setup_crew(dream)
        res = dreamAnalysisCrew.kickoff()
    except Exception as e:
        inMemoryStore.appendEvent(jobId, 'event crew kickoff failed')
        inMemoryStore.updateJobStatus(jobId, 'ERROR')
        inMemoryStore.updateJobAnalysisSummary(jobId, str(e))
        print(str(e))
        return {"status":"failed"}
    inMemoryStore.updateJobStatus(jobId, 'COMPLETE')
    inMemoryStore.updateJobAnalysisSummary(jobId, res)
    inMemoryStore.appendEvent(jobId, 'COMPLETE')
    print(jobId)

def authDecoParams(reqType='GET'):
    def authDecorator(func):
        print("lmaolmaolmaolmao",reqType)
        @wraps(func)
        def decorator(*args, **kwargs):
            if reqType=='GET':
                userId = request.args.get('req')
            elif reqType=='POST':
                reqData = request.json
                if not 'currentUserId' in reqData:
                    return {"status":"unauthorized"}
                userId = reqData['currentUserId']
            else:
                return {"status":"invalid_method"}
            print(userId)
            supabase = SingleDb.getInstance()
            res = supabase.table('UserTier').select('tier').filter('clerkId', 'eq', userId).execute()
            print("#############################",res)
            try:
                data = res.data
                if data and data[0]['tier']!='admin':
                    return {"status":"unauthorized"}
                return func(*args, **kwargs)
            except:
                return {'status':'auth_err'}
        return decorator
    return authDecorator

@app.route('/api/startsuperanalysis', methods=['POST'])
@authDecoParams('POST')
def startSuperAnalysis():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    dream = data['dreamWithContext']
    jobId = str(uuid4())
    t = Thread(target=kickoffCrew, args=(jobId, dream))
    try:
        t.start()
    except Exception as e:
        print(str(e))
        return {"status":"failed"}
    return jsonify({'jobId':jobId})

@app.route('/api/startanalysis', methods=['POST'])
def startAnalysis():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    dream = data['dreamWithContext']
    jobId = str(uuid4())
    t = Thread(target=kickoffCrewPremium, args=(jobId, dream))
    try:
        t.start()
    except Exception as e:
        print(str(e))
        return {"status":"failed"}
    return jsonify({'jobId':jobId})


@app.route('/api/dream/<jobId>', methods = ['GET'])
def getDreamEventsByJobId(jobId):
    inMemoryStore = SingletonInMemoryEvents.getSingleInstance()
    lock = inMemoryStore.getLock()
    job = inMemoryStore.getJob(jobId)
    if not job:
        abort(404, description="job doesnt exist")
    try:
        result = str(job.analysisSummary)
    except:
        result = ''
    return jsonify({
        'jobId':jobId,
        'status':job.status,
        'raw':job.rawAnalysis,
        'analysis':result,
        'events':[{"timestamp":event.timestamp.isoformat(), "data":event.data} for event in job.events]
    })

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
                "content": f'''{data['dreamWithContext']} extract the relevant jungian symbols from the above dream and return an array list containing only symbols, in the following
output format: "symbols":["symbol1", "symbol2", "symbol3"], make sure to only respond with an array containing single worded symbols in the given format''',
            }
    chat_completion = client.chat.completions.create(
        messages=[
obj
        ],
        model="mixtral-8x7b-32768",
    )


    text=chat_completion.choices[0].message.content
# Using regular expression to find the list
    list_pattern = re.compile(r'\[([^\[\]]+)\]')
    match = list_pattern.search(text)

    if match:
        # Extracting the list
        extracted_list = match.group(1)

        # Splitting the string to get individual items
        items = extracted_list.split(',')

        # Stripping extra spaces and quotes from each item
        items = [item.strip(' " ') for item in items]


        return {"items":items}
    else:
        print("No list found in the string.")
        return {"analysis":"nolist"}

@app.route('/getscraped', methods=['GET'])
def getscraped():
    response = requests.get('https://marinafw.com/mountain/#:~:text=THE%20ARCHETYPE%20OF%20THE%20MOUNTAIN,earth%2C%20mundane%20and%20numinous',headers={'User-Agent': 'Mozilla/5.0'})
    soup = bs4.BeautifulSoup(response.text,'lxml')
    allText = soup.body.get_text(' ', strip=True)
    print(allText)
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    obj =             {
                "role": "user",
                "content": f'''{allText} Task: retrieve all the relevant info and use direct quotations for expanding on the mountain symbol in a jungian context, there should not be a single mention of the article the text being retrived from an article or a blog or a post''',
            }
    chat_completion = client.chat.completions.create(
        messages=[
obj
        ],
        model="mixtral-8x7b-32768",
    )
    return {"lol":chat_completion.choices[0].message.content}

@app.route('/getlinks', methods=['GET'])
def getlinks():
    url = "https://google.serper.dev/search"

    payload = json.dumps({
    "q": "jungian interpretation mountain"
    })
    headers = {
    'X-API-KEY': 'a88471bb323dabc70364da234a1f0f6cdec01aac',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    link = ""
    data = response.json()
    print("helo")
    print(type(data), "@@@@@@@@@@@@@@@@@@@@@", data)
    try:
        if 'organic' in data:
            print("helo")
            arr = data['organic']
            print("helo")
            if len(arr)>0:
                print("helo")
                link = arr[0]['link']
                title = arr[0]['title']
                print("helo")
                print(link, title)
    except Exception as e:
        print(e)
        pass
    return data


@app.route('/api/startinterpretation', methods=['POST'])
def startInterpretation():
    data = request.json
    if 'dreamWithContext' not in data or len(data['dreamWithContext'])==0:
        return {"status": "empty dream"}
    print("apapapapapapappapapa!!!!!!!!!!!!!!!!!!!!!!",  data['dreamWithContext'])
    #dream = "I went to a mountain with my extended family and we climbed it in excitement without thinking much, once we reached the top we realised that we arent skilled enough to get down as it was very steep, on the mountain i realised that i can also fly and somehow i flew and reached a marshy land where i feared the snakes, luckily i survived"
    jobId = str(uuid4())
    obj = SymbolInterpreter()
    t = Thread(target=obj.interpret, args=(jobId, data['dreamWithContext']))
    try:
        t.start()
    except Exception as e:
        print(str(e))
        return {"status":"failed"}
    return jsonify({'jobId':jobId})

@app.route('/api/checkinterpretation', methods=['GET'])
def checkInterpretation():
    jobId = request.args.get('jobId')
    kv = SingletonJobsKv.getInstance()
    job = None
    with kv.getLock():
        job = kv.getJobForApi(jobId)
    return jsonify({'job':job})

@app.route('/kvflow', methods=['GET'])
def kvflow():
    print("lmaolmaolmaolmao")
    kv = SingletonJobsKv.getInstance()
    print("heloleoeo")
    with kv.getLock():
        print("1111111111")
        kv.appendEvent('1234', "started")
        print("222222222")
        event = kv.updateJobSymbols('1234', ["symbol1", "symbol2", "symbol3"])
        kv.appendEvent('1234', str(event))
        event = kv.updateJobSymbolLinks('1234', [SymbolLink("mountain","link"), SymbolLink("lol","link")])
        kv.appendEvent('1234', str(event))
        event = kv.updateJobResult('1234', 'final_result')
        kv.appendEvent('1234', str(event))
        event = kv.updateJobStatus('1234', "completed")
        job = kv.getJob('1234')
        print(job)
    return {"job":job}

if __name__=='__main__':
    app.run(debug=True, port=8000)

{
    "lol": "{\"searchParameters\":{\"q\":\"jungian interpretation mountain\",\"type\":\"search\",\"engine\":\"google\"},\"answerBox\":{\"snippet\":\"The mountain has the symbolism that aims for the mind's inner enhancement and the absolute world of self-consciousness (Elide, 1959). Jung's individuation is to become 'Self,' demonstrating and incorporating the mind that we bring to the world when we are born.\",\"snippetHighlighted\":[\"aims for the mind's inner enhancement and the absolute world of self-consciousness\"],\"title\":\"Mountain: Maternal Symbolism of Conceiving Individuation\",\"link\":\"https://www.e-jsst.org/upload/pdf/jsst-6-63.pdf\"},\"organic\":[{\"title\":\"Carl Jung And Mountains Anthology\",\"link\":\"https://carljungdepthpsychologysite.blog/2020/10/29/mountains-anthology/\",\"snippet\":\"Your heights are your own mountain, which belongs to you and you alone. There you are individual and live your very own life. If you live your ...\",\"date\":\"Oct 29, 2020\",\"position\":1},{\"title\":\"Symbolism of Mountains | symbolreader\",\"link\":\"https://symbolreader.net/2021/07/31/symbolism-of-mountains/\",\"snippet\":\"For Jung, mountains (and other features of the landscape) symbolized \u201cthe essence of God.\u201d Snow-capped mountains are indeed nothing less than ...\",\"date\":\"Jul 31, 2021\",\"position\":2},{\"title\":\"Climbing the Alchemical Mountain | - Psyche and Nature\",\"link\":\"https://psycheandnature.com/2016/10/09/climbing-the-alchemical-mountain/\",\"snippet\":\"Jung (1958/1968) writes, \u201cThe prima materia comes from the mountain. This is where everything is upside down: 'And the top of this rock is ...\",\"date\":\"Oct 9, 2016\",\"position\":3},{\"title\":\"Carl Jung and \\\"The Holiness of Mountains\\\"\",\"link\":\"http://tomandatticus.blogspot.com/2008/04/carl-jung-and-holiness-of-mountains.html\",\"snippet\":\"One is in the introduction, written by Wayne Grady: \u201cJung believed that humanity took 'a wrong turn' when it lost contact with its past and with ...\",\"date\":\"Apr 24, 2008\",\"attributes\":{\"Missing\":\"interpretation | Show results with:interpretation\"},\"position\":4},{\"title\":\"Mountain dream interpretation? : r/Jung - Reddit\",\"link\":\"https://www.reddit.com/r/Jung/comments/b4wg3p/mountain_dream_interpretation/\",\"snippet\":\"The dream: I lived in a city with all all of the people on the earth. On one side of the city was the sea. There was no harbor, no boats, just ...\",\"date\":\"Mar 25, 2019\",\"sitelinks\":[{\"title\":\"Dream predicting one's death : r/Jung - Reddit\",\"link\":\"https://www.reddit.com/r/Jung/comments/g9lmfb/dream_predicting_ones_death/\"},{\"title\":\"Scenery from a dream. CG Jung himself made an appearance...wise ...\",\"link\":\"https://www.reddit.com/r/Jung/comments/sh1i57/scenery_from_a_dream_cg_jung_himself_made_an/\"},{\"title\":\"Celeste and Jungian Psychology : r/celestegame - Reddit\",\"link\":\"https://www.reddit.com/r/celestegame/comments/ac6rca/celeste_and_jungian_psychology/\"},{\"title\":\"Dream about a mountain and meadow : r/Jung - Reddit\",\"link\":\"https://www.reddit.com/r/Jung/comments/1btpdrt/dream_about_a_mountain_and_meadow/\"}],\"position\":5},{\"title\":\"Carl Jung and the Psychology of Dreams - Academy of Ideas\",\"link\":\"https://academyofideas.com/2023/06/carl-jung-and-the-psychology-of-dreams-messages-from-the-unconscious/\",\"snippet\":\"Jung's colleague, an amateur mountaineer, told Jung of the following dream: He was climbing a mountain, and the higher he climbed, the better he ...\",\"date\":\"Jun 20, 2023\",\"position\":6},{\"title\":\"Blog -\",\"link\":\"http://www.selfdiscoverypsychotherapy.com/blog/\",\"snippet\":\"A mountain can be considered to be a symbol of the Self. It's appearance however typically comes with other symbols, for example in a dream that ...\",\"date\":\"Feb 19, 2016\",\"position\":7},{\"title\":\"Mountain, The | SpringerLink\",\"link\":\"https://link.springer.com/10.1007/978-1-4614-6086-2_442\",\"snippet\":\"Mountains symbolize constancy, eternity, firmness, and stillness. They have been used to represent the state of full consciousness: in Nepal, the sacred ...\",\"position\":8},{\"title\":\"Lessons of Jung's Encounter with Native Americans - The Jung Page\",\"link\":\"https://jungpage.org/learn/articles/analytical-psychology/881-lessons-of-jungs-encounter-with-native-americans\",\"snippet\":\"Jung interpreted Mountain Lake's reference to the restlessness of whites as describing their \\\"insatiable lust to lord it in every land,\\\" and ...\",\"date\":\"Oct 27, 2013\",\"position\":9}],\"peopleAlsoAsk\":[{\"question\":\"What does the mountain symbolize spiritually?\",\"snippet\":\"It is a universal symbol of the nearness of God, as it surpasses ordinary humanity and extends toward the SKY and the heavens. It symbolizes constancy, permanence, motionlessness, and its peak spiritually signifies the state of absolute consciousness.\",\"title\":\"Mountain\",\"link\":\"https://public.websites.umich.edu/~umfandsf/symbolismproject/symbolism.html/M/mountain.html\"},{\"question\":\"What did the mountain symbolize?\",\"snippet\":\"Many ancient cultures considered the mountain the \u201cCenter of the World.\u201d It often serves as a cosmic axis linking heaven and earth and providing \u201corder\u201d to the universe. Mountains evoke a special sense of awe and power and no single image or meaning can capture or express every facet of its symbolic significance.\",\"title\":\"Mountain, The | SpringerLink\",\"link\":\"https://link.springer.com/10.1007/978-1-4614-6086-2_442\"},{\"question\":\"What is the archetype of mountains?\",\"snippet\":\"THE ARCHETYPE OF THE MOUNTAIN The main symbol that the mountain encapsulates is being the place of reunion of the opposites (heaven and earth, mundane and numinous).\",\"title\":\"The Mountain \u2014 Marina F. W.\",\"link\":\"https://marinafw.com/mountain/\"},{\"question\":\"What does the mountain range symbolize?\",\"snippet\":\"Some of the things that a mountain or range of mountains can symbolize: obstacles. climbing over one or passing through a range indicates . overcoming obstacles or making progress.\",\"title\":\"Mountain | Symbolism Wiki | Fandom\",\"link\":\"https://symbolism.fandom.com/wiki/Mountain\"}]}"
}
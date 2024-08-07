
import chainlit as cl

from duckduckgo_search import DDGS

@cl.step
async def ddgs_news(query):

    results = DDGS(proxy="http://127.0.0.1:5035").news(query, max_results=5)

    results_str = ''

    counter = 1
    for item in results:
        results_str += str(counter) + ". " + item['source'] + ':\n'
        results_str += item['body'] + '\n\n'
        counter +=1

    print(results_str)

    return results_str


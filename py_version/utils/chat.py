from openai import OpenAI
import time
import os
from utils.logger import Logger
logger = Logger.get_logger('Chat')
client = OpenAI(api_key=os.environ['OPENAI_KEY'])
class Chat:

    @staticmethod
    def chat_with_llm(prompt):
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {
                        'role':'user',
                        'content':[
                            {'type':'text',
                             'text':prompt
                            }
                        ]
                    }
                ],
                temperature=0.7
            )
            res = response.choices[0].message.content
            logger.info(f'Screen Summary:{res}')
            return res
        except Exception as e:
            logger.warning(f'Can not connect to llm:{e}')


import os
import openai 

from dotenv import load_dotenv
load_dotenv()

from op_structures import CodeSummmary



class api_registry:

    def __init__(self, server : str = "openai" ) -> None:

        self.server = server

        if server == "openai":
            
            self.default_model = "gpt-5-nano"
            
            try:
                self.client = openai.OpenAI()

            except Exception as e:
                raise Exception('( during openai api call ) : %s'%e)
            
        elif server == "gemini": 

            ...

        
    def get_response(self, prompt : str, model_choice : str = None):

        if not model_choice:
            model_choice = self.default_model

        response = self.client.responses.parse(input=prompt, model=model_choice, text_format=CodeSummmary)

        return getattr(response, "code_summary", response)
        

        
                
        
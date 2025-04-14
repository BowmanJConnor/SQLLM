from os.path import exists
import requests
import json

FCALL_PROMPT = """
You are a software assistant that can call functions and retrieve data to assist users.
All responses should be function calls in JSON format as follows:
[{\"fCall\" : \"functionName\", \"paramName\" : \"argument\", \"paramName\" : \"argument\"}]
where functionName is replaced with the name of the function (only alphanumeric characters),
each paramName is replaced with the real parameter name for the given function, and argument is replaced with the
corresponding argument value for the parameter. Functions can have multiple different parameters based on their template.
More than one function can be called in a row by responding with a comma delimited list in square brackets, i.e. \"[{},{},{}]\"
If functionality is unavailable to fulfill a request, or the user did not ask a quetion related to the functions, simply respond \"INVALID REQUEST\".

The available functions to call are listed below in the format
[(Function Name, Parameter 1, Parameter 2, etc),
Function Description, Return Value Description]:

[(addUser, userName), This function adds a user with name userName to the database, returns 1 on success and 0 on failure].
[(removeUser, userName), This function removes the user with name userName from the database, returns 1 on success and 0 on failure].
"""
ELABORATE_PROMPT = """
You are part of a software system that can call functions and retrieve data to assist users.
Your job is to read what the user input to the system, read the system messages that are returned after processing user input,
and explain to the user what happened on the system side. The user input is the previous input to the system. It has already been processed.
Keep your responses short and to the point. The system messages are provided here: 
"""


def add_user(fcall):
    if not "userName" in fcall:
        return "Failed to add user... userName field was not provided."
    # TODO: SQL logic goes here
    return f"Successfully added {fcall['userName']} to the database." 

def remove_user(fcall):
    if not "userName" in fcall:
        return "Failed to remove user... userName field was not provided."
    return f"Successfully removed {fcall['userName']} from the database." 

fcall_map = {"addUser" : add_user,
             "removeUser" : remove_user}

def call_func(fcall):
    if not ("fCall" in fcall):
        return f"LLM did not properly format function call request."
    if not fcall["fCall"] in fcall_map:
        return f"{fcall['fCall']} is not a valid function for this system."
    return fcall_map[fcall['fCall']](fcall) # call function corresponding to fCall with entire fcall as argument

class Llama4MaverickIO:
    def __init__(self, api_key_file):
        self.fcall_prompt = FCALL_PROMPT
        if exists(api_key_file):
            with open(api_key_file, 'r') as key_file:
                self.api_key = key_file.readline().strip() # First line of file should contain key
        else:
            print("API key file does not exist... requests will fail")
            self.api_key = ""

    def get_elaborate_prompt(self, fcall_responses):
        return ELABORATE_PROMPT + "[" + ", ".join(fcall_responses) + "]"

    def elaborate(self, fcall_responses, user_input):
        elaborate_response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },

            data=json.dumps({
                "model": "meta-llama/llama-4-maverick:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                        {
                            "type": "text",
                            "text": user_input
                        },
                        ]
                    },
                    {
                        "role": "system",
                        "content": [
                        {
                            "type": "text",
                            "text": self.get_elaborate_prompt(fcall_responses)
                        },
                        ]
                    },
                ],
            })
        )

        elaborate_resp_json = elaborate_response.json()
        if "choices" in elaborate_resp_json and len(elaborate_resp_json["choices"]) > 0 and "message" in elaborate_resp_json["choices"][0]:
            elaborate_msg = elaborate_resp_json["choices"][0]["message"]
            if "content" in elaborate_msg:
                elaboration = elaborate_msg["content"]
                return json.dumps(elaboration), 200 # Get elaboration text from LLM based on fcall responses
        
        return json.dumps({"error": "Bad LLM Elaboration"}), 400
        
    def ask(self, user_input):
        fcall_response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },

            data=json.dumps({
                "model": "meta-llama/llama-4-maverick:free",
                "messages": [
                    {
                        "role": "system",
                        "content": [
                        {
                            "type": "text",
                            "text": self.fcall_prompt
                        },
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                        {
                            "type": "text",
                            "text": user_input
                        },
                        ]
                    }
                ],
            })
        )

        fcall_resp_json = fcall_response.json()
        if "choices" in fcall_resp_json and len(fcall_resp_json["choices"]) > 0 and "message" in fcall_resp_json["choices"][0]:
            fcall_msg = fcall_resp_json["choices"][0]["message"]
            if "content" in fcall_msg:
                fcalls_content = fcall_msg["content"]
                # Try to load fcall content into a list
                try:
                    fcalls = json.loads(fcalls_content)
                except:
                    return json.dumps({"error": "Invalid Request"}), 400

                fcall_responses = []
                for fcall in fcalls:
                    fcall_responses.append(call_func(fcall))
                
                return self.elaborate(fcall_responses, user_input) # Get elaboration response from LLM based on fcall responses and user input
        
        return json.dumps({"error": "Bad LLM Response"}), 400
        
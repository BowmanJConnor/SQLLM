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

def add_user(fcall):
    if not "userName" in fcall:
        return "Failed to add user... userName field was not provided."
    # TODO: SQL logic goes here
    return f"Successfully added {fcall['userName']} to the database." 

def remove_user(fcall):
    if not "userName" in fcall:
        return "Failed to remove user... userName field was not provided."
    return f"Successfully added {fcall['userName']} to the database." 

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
                # Try to call all functions in fcalls
                try:
                    fcalls = json.loads(fcalls_content)
                except:
                    return json.dumps({"error": "Invalid Request"}), 400

                fcall_responses = []
                for fcall in fcalls:
                    fcall_responses.append(call_func(fcall))
        else:
            return json.dumps({"error": "Bad LLM Response"}), 400
        
        return json.dumps(fcall_responses), 200
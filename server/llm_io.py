from os.path import exists
import requests
import json
from db import db, User

FUNCTION_DETAILS = """
[(addUser, userName, age?), This function adds a user with name userName and optional age to the database].
[(removeUser, userName), This function removes the user with name userName from the database].
[(modifyUser, userName, age?), This function modifies the user with name userName to change any fields provided].
[(retrieveUser, userName), This function retrieves the user with name userName from the database].
"""

FCALL_PROMPT = """
You are a software assistant that can call functions and retrieve data to assist users.
All responses should be function calls in JSON format as follows:
[{\"fCall\" : \"functionName\", \"paramName\" : \"argument\", \"paramName\" : \"argument\"}]
where functionName is replaced with the name of the function (only alphanumeric characters),
each paramName is replaced with the real parameter name for the given function, and argument is replaced with the
corresponding argument value for the parameter. Functions can have multiple different parameters based on their template.
Parameters followed by a \"?\" are optional... they are not required to be included in the fCall unless the user specifies.
If the user does specify an optional argument, it should be included, but without the \"?\" in the parameter name.
More than one function can be called in a row by responding with a comma delimited list in square brackets, i.e. \"[{},{},{}]\"
If functionality is unavailable to fulfill a request, or the user is asking a question or making a comment, simply respond \"ELABORATE\".
NOTE: Usernames in function calls should always be properly capitalized.

The available functions to call are listed below in the format
[(Function Name, Parameter 1, Parameter 2, etc), Function Description]:

""" + FUNCTION_DETAILS

ELABORATE_PROMPT = """
You are part of a software system that can call functions and retrieve data to assist users.
Your job is to read what the user input to the system, read the system messages that are returned after processing user input,
and explain to the user what happened on the system side. The user input is the previous input to the system. It has already been processed.
If there are no system messages provided, i.e. [], then no system functions were called.
If the user requested for a system operation, explain that it was not performed. 
Otherwise, just respond to the user as if they are talking to you, without mentioning the system.
Keep your responses short and to the point. The system messages are provided here: 
"""

USER_CONTEXT_PREFACE = """
This was the previous message from the user:
"""

LLM_CONTEXT_PREFACE = """
This was your previous reply:
"""


# fCall functions start here

def add_user(fcall):
    return_str = "Attempting to add user..."

    if not "userName" in fcall:
        return return_str + " Failed to add user... userName field was not provided."

    user = User(name=fcall["userName"])
    return_str += f" Successfully added {fcall['userName']} to the database."

    if "age" in fcall:
        try:
            user.age = int(fcall["age"])
            return_str += f" Successfully set age of {fcall['userName']} to {user.age}."
        except:
            pass

    db.session.add(user)
    db.session.commit()
    return return_str


def remove_user(fcall):
    return_str = "Attempting to remove user..."

    if not "userName" in fcall:
        return return_str + " Failed to remove user... userName field was not provided."

    user = User.query.filter_by(name=fcall['userName']).first()
    if not user:
        return_str += f" Failed to remove user \"{fcall['userName']}\" because they are not in the database."
    else:
        db.session.delete(user)
        db.session.commit()
        return_str += f" Successfully removed {fcall['userName']} from the database." 

    return return_str


def modify_user(fcall):
    return_str = "Attempting to modify user..."

    if not "userName" in fcall:
        return return_str + " Failed to modify user... userName field was not provided."

    user = User.query.filter_by(name=fcall['userName']).first()
    
    if not user:
        return_str += f" Failed to modify user \"{fcall['userName']}\" because they are not in the database."
    
    if "age" in fcall:
        try:
            user.age = int(fcall["age"])
            db.session.commit()
            return_str += f" Successfully modified age of {fcall['userName']} to {user.age}."
        except:
            pass
    
    return return_str

def retrieve_user(fcall):
    return_str = "Attempting to retrieve user..."

    if not "userName" in fcall:
        return return_str + " Failed to retrieve user... userName field was not provided."

    user = User.query.filter_by(name=fcall['userName']).first()
    
    if not user:
        return_str += f" Failed to retrieve user \"{fcall['userName']}\" because they are not in the database."
    else:
        return_str += f" Retrieved Data: [ID: {user.id}, Name: {user.name}, Age: {user.age}]"

    return return_str


# fCall functions are mapped here
fcall_map = {"addUser" : add_user,
             "removeUser" : remove_user,
             "modifyUser" : modify_user,
             "retrieveUser" : retrieve_user}

def call_func(fcall):
    if not ("fCall" in fcall):
        return f"LLM did not properly format function call request."
    if not fcall["fCall"] in fcall_map:
        return f"{fcall['fCall']} is not a valid function for this system."
    return fcall_map[fcall['fCall']](fcall) # call function corresponding to fCall with entire fcall as argument



# LLM interface defined here
class Llama4MaverickIO:
    def __init__(self, api_key_file):
        self.fcall_prompt = FCALL_PROMPT
        if exists(api_key_file):
            with open(api_key_file, 'r') as key_file:
                self.api_key = key_file.readline().strip() # First line of file should contain key
        else:
            print("API key file does not exist... requests will fail")
            self.api_key = ""
        self.prev_elaboration = ""
        self.prev_user_input = ""

    def get_elaborate_prompt(self, fcall_responses):
        return ELABORATE_PROMPT + "[" + ", ".join(fcall_responses) + "]"

    def get_context(self):
        return " ".join([USER_CONTEXT_PREFACE, self.prev_user_input, LLM_CONTEXT_PREFACE, self.prev_elaboration])

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
                        "role": "assistant",
                        "content": [
                        {
                            "type": "text",
                            "text": self.get_context() # Supply LLM with context of previous messages
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
        self.prev_user_input = user_input # Store previous user input for later
        elaborate_resp_json = elaborate_response.json()
        print(elaborate_resp_json)
        if "choices" in elaborate_resp_json and len(elaborate_resp_json["choices"]) > 0 and "message" in elaborate_resp_json["choices"][0]:
            elaborate_msg = elaborate_resp_json["choices"][0]["message"]
            if "content" in elaborate_msg:
                elaboration = elaborate_msg["content"]
                return json.dumps(elaboration), 200 # Get elaboration text from LLM based on fcall responses
        
        return json.dumps({"error": "Bad LLM Response"}), 400
        
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
                        "role": "assistant",
                        "content": [
                        {
                            "type": "text",
                            "text": self.get_context() # Supply LLM with context of previous messages
                        },
                        ]
                    },
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

        fcall_responses = []
        fcall_resp_json = fcall_response.json()
        print(fcall_resp_json)
        if "choices" in fcall_resp_json and len(fcall_resp_json["choices"]) > 0 and "message" in fcall_resp_json["choices"][0]:
            fcall_msg = fcall_resp_json["choices"][0]["message"]
            if "content" in fcall_msg:
                fcalls_content = fcall_msg["content"]
                # Try to load fcall content into a list
                try:
                    fcall_responses = []
                    fcalls = json.loads(fcalls_content)
                    for fcall in fcalls:
                        fcall_responses.append(call_func(fcall))
                except:
                    fcall_responses = []

        print("fCall results: ", fcall_responses)
        # Get elaboration response from LLM based on fcall responses and user input
        elaboration = self.elaborate(fcall_responses, user_input)
        self.prev_elaboration = elaboration[0] # saves previous LLM elaboration for context TODO: make this more robust
        return elaboration
        
# SQLLM
Web LLM Interface with access to SQL Database



To run the SQLLM demo, an [OpenRouter](https://openrouter.ai/) API key must be stored in a file referred to by `API_KEY_FILE` in the Makefile. 
Model training must be enabled on your OpenRouter account to allow the Llama4Maverick model to be used for the demo.

First, start the postgres database with `make start_db`.

Next, start the SQLLM server with `make sqllm`.

Navigate to [127.0.0.1:5000](http://127.0.0.1:5000/) in a browser to visit the webpage and interact with the database through the LLM. 

To remove the database after exiting the demo, run `make remove_db`. 


Created by Connor Bowman.

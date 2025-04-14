CONTAINER_NAME ?= "sqllm_pg"
PG_USER ?= "sqllm_user"
PG_PASS ?= "sqllm_pass"
PG_DB ?= "sqllm_db"

API_KEY_FILE ?= "$(HOME)/API_KEYS/openrouter.key"

sqllm:
	python3 server/server.py $(API_KEY_FILE)

start_db:
	sudo docker run --name $(CONTAINER_NAME) -e POSTGRES_USER=$(PG_USER) -e POSTGRES_PASSWORD=$(PG_PASS) -e POSTGRES_DB=$(PG_DB) -p 5432:5432 -d postgres

stop_db:
	sudo docker stop $(CONTAINER_NAME)

remove_db:
	sudo docker rm -f $(CONTAINER_NAME)
.PHONY: setup schema ingest build supersede serve eval test ui
setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
schema:
	python -m scripts.apply_schema
ingest:
	python -m scripts.ingest
build:
	python -m scripts.build_graph
supersede:
	python -m scripts.run_supersession
serve:
	uvicorn backend.app.main:app --reload --port 8000
eval:
	python -m scripts.run_eval
test:
	pytest backend/tests -q
ui:
	cd frontend && npm install && npm run dev

from backend.app.graph.db import get_db
from backend.app.llm.provider import get_llm
from backend.app.reasoning.supersession import run_supersession

if __name__ == "__main__":
    print(run_supersession(get_db(), get_llm()))

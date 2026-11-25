from langsmith import Client

from app.core.config import get_settings
from app.services.llm_service import configure_tracing
from scripts.evaluation_cases import CASES


def main():
    settings = get_settings()
    configure_tracing(settings)
    if not settings.langsmith_api_key.get_secret_value():
        raise SystemExit("Configure LANGSMITH_API_KEY in backend/.env before uploading.")
    client = Client(api_key=settings.langsmith_api_key.get_secret_value())
    name = "careerpilot-synthetic-v1"
    if client.has_dataset(dataset_name=name):
        raise SystemExit(
            "Dataset already exists. Use it or delete it intentionally in LangSmith before recreating."
        )
    dataset = client.create_dataset(
        dataset_name=name, description="Ten synthetic CareerPilot regression cases"
    )
    client.create_examples(
        dataset_id=dataset.id,
        inputs=[{k: v for k, v in c.items() if k != "expected"} for c in CASES],
        outputs=[c["expected"] for c in CASES],
    )
    print(f"Created {name} with {len(CASES)} examples.")


if __name__ == "__main__":
    main()

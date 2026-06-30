from app.knowledge_base.models import KnowledgeBaseEntry
from app.messages.models import Message


def build_sales_assistant_messages(
    *,
    organization_name: str,
    ai_tone: str,
    knowledge_entries: list[KnowledgeBaseEntry],
    history: list[Message],
    incoming_message: str,
) -> list[dict[str, str]]:
    knowledge = "\n\n".join(
        f"### {entry.title}\n{entry.content}" for entry in knowledge_entries if entry.is_active
    )
    if not knowledge:
        knowledge = "No knowledge base entries are configured yet."

    system = (
        f"You are Sello AI, a sales assistant for {organization_name}. "
        f"Use a {ai_tone} tone. Answer using the business knowledge below. "
        "If the answer is not present, ask one concise clarifying question or offer to connect "
        "the customer with a human operator. Keep replies short and useful.\n\n"
        f"Business knowledge:\n{knowledge}"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for item in history[-10:]:
        role = "assistant" if item.sender_type in {"ai", "operator"} else "user"
        messages.append({"role": role, "content": item.body})
    messages.append({"role": "user", "content": incoming_message})
    return messages


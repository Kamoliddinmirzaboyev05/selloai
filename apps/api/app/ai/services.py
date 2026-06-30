from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.groq import GroqClient
from app.ai.prompts import build_sales_assistant_messages
from app.knowledge_base.services import list_active_entries
from app.messages.services import list_messages
from app.organizations.models import Organization
from app.settings.models import OrganizationSettings


async def generate_ai_reply(
    session: AsyncSession,
    *,
    organization: Organization,
    settings: OrganizationSettings,
    conversation_id: str,
    incoming_message: str,
    client: GroqClient | None = None,
) -> str:
    knowledge_entries = await list_active_entries(session, organization.id)
    history = await list_messages(session, conversation_id, limit=12)
    messages = build_sales_assistant_messages(
        organization_name=organization.name,
        ai_tone=settings.ai_tone,
        knowledge_entries=knowledge_entries,
        history=history,
        incoming_message=incoming_message,
    )
    groq_client = client or GroqClient()
    return await groq_client.chat_completion(messages)


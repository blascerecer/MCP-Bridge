from lmos_openai_types import CreateChatCompletionRequest, CreateChatCompletionResponse
from .genericHttpxClient import client
from mcp_clients.McpClientManager import ClientManager
from tool_mappers import mcp2openai
from loguru import logger
import json


async def chat_completions(
    request: CreateChatCompletionRequest,
) -> CreateChatCompletionResponse:
    """performs a chat completion using the inference server"""

    request.tools = []

    for _, session in ClientManager.get_clients():
        tools = await session.session.list_tools()
        for tool in tools.tools:
            request.tools.append(mcp2openai(tool))

    response = CreateChatCompletionResponse.model_validate_json(
        (
            await client.post(
                "/chat/completions",
                json=request.model_dump(
                    exclude_defaults=True, exclude_none=True, exclude_unset=True
                ),
            )
        ).text
    )

    if response.choices[0].message.tool_calls is not None:
        for tool_call in response.choices[0].message.tool_calls.root:
            logger.debug(f"tool call: {tool_call.function.model_dump()}")

            # FIXME: this can probably be done in parallel using asyncio gather
            session = await ClientManager.get_client_from_tool(tool_call.function.name)
            tool_call_result = await session.call_tool(
                name=tool_call.function.name, 
                arguments=json.loads(tool_call.function.arguments)
            )

            logger.debug(f"tool call result for {tool_call.function.name}: {tool_call_result.model_dump()}")

    return response

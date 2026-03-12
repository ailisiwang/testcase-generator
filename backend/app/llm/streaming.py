"""Streaming utilities for LLM output"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from app.llm.base import get_llm_provider


class StreamManager:
    """Manage streaming responses"""
    
    def __init__(self):
        self._streams: Dict[str, asyncio.Queue] = {}
    
    def create_task(self, task_id: Optional[str] = None) -> str:
        """Create a new streaming task"""
        if task_id is None:
            task_id = str(uuid.uuid4())
        self._streams[task_id] = asyncio.Queue()
        return task_id
    
    async def put(self, task_id: str, data: Dict[str, Any]):
        """Add data to stream"""
        if task_id in self._streams:
            await self._streams[task_id].put(data)
    
    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get data from stream"""
        if task_id in self._streams:
            return await self._streams[task_id].get()
        return None
    
    async def stream_generator(self, task_id: str) -> AsyncGenerator[str, None]:
        """Create a streaming response generator"""
        while task_id in self._streams:
            try:
                data = await asyncio.wait_for(
                    self._streams[task_id].get(), 
                    timeout=30
                )
                yield json.dumps(data, ensure_ascii=False) + "\n"
            except asyncio.TimeoutError:
                break
        
        # Clean up
        if task_id in self._streams:
            del self._streams[task_id]
    
    def close(self, task_id: str):
        """Close a streaming task"""
        if task_id in self._streams:
            del self._streams[task_id]


# Global stream manager
stream_manager = StreamManager()


async def stream_generate_cases(
    provider: str,
    api_key: str,
    model_name: str,
    requirement: str,
    system_fields: list,
    count: int = 5,
    api_base_url: Optional[str] = None,
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """
    Stream generate test cases
    
    Args:
        provider: LLM provider name
        api_key: API key
        model_name: Model name
        requirement: Requirement description
        system_fields: Field configurations
        count: Number of cases to generate
        api_base_url: Optional API base URL
        temperature: Temperature setting
    
    Yields:
        JSON formatted stream chunks
    """
    task_id = stream_manager.create_task()
    
    try:
        # Get LLM provider
        llm = get_llm_provider(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            api_base_url=api_base_url,
            temperature=temperature
        )
        
        # Build prompt for test case generation
        field_names = [f["field_label"] for f in system_fields]
        field_types = {f["field_name"]: f["field_type"] for f in system_fields}
        
        prompt = f"""请根据以下需求生成{count}条测试用例。

需求描述：
{requirement}

用例字段：
{', '.join(field_names)}

请以JSON数组格式返回，每个用例包含以下字段：
{json.dumps([f"{f['field_name']} ({f['field_label']})" for f in system_fields], ensure_ascii=False, indent=2)}

要求：
1. 每条用例要完整覆盖功能点
2. 包括正常场景和异常场景
3. 测试步骤要清晰可执行
4. 预期结果要明确

请直接返回JSON数组，不要其他解释："""
        
        await stream_manager.put(task_id, {
            "type": "start",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Stream the response
        case_count = 0
        async for chunk in llm.stream(prompt):
            await stream_manager.put(task_id, {
                "type": "chunk",
                "content": chunk,
                "timestamp": datetime.utcnow().isoformat()
            })
            case_count += 1
        
        # Try to parse the result
        try:
            # Get full response would require accumulating chunks
            # For streaming, we send the chunks and let client parse
            await stream_manager.put(task_id, {
                "type": "complete",
                "count": case_count,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            await stream_manager.put(task_id, {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
    finally:
        # Yield remaining data
        async for data in stream_manager.stream_generator(task_id):
            yield data


async def stream_generate_from_file(
    provider: str,
    api_key: str,
    model_name: str,
    file_content: str,
    system_fields: list,
    count: int = 5,
    api_base_url: Optional[str] = None,
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Stream generate test cases from file content"""
    
    prompt = f"""请根据以下需求文档生成{count}条测试用例。

需求文档内容：
{file_content}

请以JSON数组格式返回测试用例。"""
    
    llm = get_llm_provider(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        api_base_url=api_base_url,
        temperature=temperature
    )
    
    async for chunk in llm.stream(prompt):
        yield json.dumps({"content": chunk}, ensure_ascii=False) + "\n"

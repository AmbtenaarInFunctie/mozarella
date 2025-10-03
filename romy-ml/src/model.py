import os
import re
from typing import Dict, Any, Optional, List
import json

from structures import ModelResponse
from openai import AsyncOpenAI

class Model:
    _system_prompt_cache: Optional[str] = None
    
    def __init__(self, model_provider: str, model_name: str): 
        self._model_name = model_name
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            default_headers={
                "HTTP-Referer": "https://github.com/mrcodepanda/romy-ml",
                "X-Title": "Romy ML"
            }
        )
        self._conversation_history: Dict[str, List[Dict[str, str]]] = {}

    def _get_system_prompt(self) -> str:
        """Get system prompt with caching"""
        if Model._system_prompt_cache is None:
            prompt_path = os.path.join(os.getcwd(), "data", "templates", "system_prompt.md")
            with open(prompt_path, "r", encoding="utf-8") as f:
                Model._system_prompt_cache = f.read()
        return Model._system_prompt_cache

    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for user"""
        return self._conversation_history.setdefault(user_id, [])
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Public method to get conversation history for user"""
        return self._get_conversation_history(user_id)
    
    def _add_to_history(self, user_id: str, role: str, content: str, citations: list = None):
        """Add message to conversation history"""
        history = self._get_conversation_history(user_id)
        message_data = {"role": role, "content": content}
        if citations is not None:
            message_data["citations"] = citations
        history.append(message_data)
        if len(history) > 10:
            self._conversation_history[user_id] = history[-10:]

    async def _preprocess_support_docs(self, support_docs: Any) -> str:
        """Format support documents for the model"""
        if not support_docs or not support_docs[0]:
            return "No support documents available."
        
        # Compile regex patterns once
        patterns = {
            'empty_link': re.compile(r'\[\]\(\)'),
            'data_image': re.compile(r'!\[.*?\]\(data:image[^)]+\)'),
            'https_image': re.compile(r'!\[.*?\]\(https://[^)]*\)'),
            'multiple_newlines': re.compile(r'\n{3,}')
        }
        
        formatted_docs = []
        for i, result in enumerate(support_docs[0], 1):
            parts = [f"## Support Document {i}"]
            
            if hasattr(result, 'metadata') and result.metadata:
                parts.append(f"**Title:** {result.metadata.get('metadata:title', 'Unknown')}")
                parts.append(f"**URL:** {result.metadata.get('metadata:original_url', 'N/A')}")
                parts.append(f"**Domain:** {result.metadata.get('metadata:domain', 'N/A')}")
                parts.append(f"**Relevance Score:** {result.score:.4f}\n")
            
            if hasattr(result, 'content') and result.content:
                content = result.content.strip()
                for pattern in patterns.values():
                    content = pattern.sub('', content)
                parts.append(f"**Content:**\n{content}")
            
            formatted_docs.append("\n".join(parts))

        return "\n\n" + "\n\n".join(formatted_docs) + "\n"

    async def _build_prompt(self, query: str, support_docs: Any) -> str:
        """Build the final prompt with query and support documents"""
        support_docs_text = await self._preprocess_support_docs(support_docs)
        
        return f"""**User Question:** {query}

        {support_docs_text}

        **INSTRUCTIONS:**
        1. Respond in the SAME LANGUAGE as the user's question
        2. Use ACTUAL URLs in inline citations: [https://full-url-here]
        3. Extract URLs from Support Document **URL** fields
        4. Return JSON with this exact structure:
        {{
        "content": "your response with inline citations",
        "citations": [
            {{
            "document_id": "URL from support doc",
            "document_title": "Title from support doc",
            "document_original_url": "URL from support doc",
            "document_domain": "Domain from support doc",
            "document_number": 1,
            "relevance_score": 0.95
            }}
        ]
        }}

        Example citation in content: "Phishing is digital fraud [https://www.kvk.nl/veilig-zakendoen/pas-op-voor-phishing/]"
        """
    
    def _parse_json_safe(self, content: str) -> dict:
        """Parse JSON, handling common LLM formatting issues"""
        
        # Remove markdown code blocks
        if "```" in content:
            content = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', content, flags=re.DOTALL)
        
        content = content.strip()
        
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fix unescaped newlines in string values
            # Find "content": "..." and escape newlines within it
            content = re.sub(
                r'("content"\s*:\s*")([^"]*?)(")',
                lambda m: m.group(1) + m.group(2).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') + m.group(3),
                content,
                flags=re.DOTALL
            )
            return json.loads(content)
    
    async def run(self, query: str, support_docs: Any, user_id: str) -> ModelResponse:
        """Generate model response for query"""
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        messages.extend(self._get_conversation_history(user_id))
        messages.append({"role": "user", "content": await self._build_prompt(query, support_docs)})
        
        completion = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=4096,
        )
        
        response_json = self._parse_json_safe(completion.choices[0].message.content)
        response = ModelResponse(**response_json)
        
        self._add_to_history(user_id, "user", query)
        # Convert Citation objects to dicts for storage
        citations_dict = [citation.model_dump() for citation in response.citations] if response.citations else None
        self._add_to_history(user_id, "assistant", response.content, citations_dict)
        
        return response

    def __str__(self):
        return f"Model({self._model_name})"
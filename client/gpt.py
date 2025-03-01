from openai import AsyncOpenAI

import json, re

class Gpt:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.temperature=0.7

    async def prompt(self, prompt, max_tokens):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=self.temperature
        )

        return response.choices[0].message.content.strip()

    def parse_json(self, data):
        cleaned = re.sub(r"```json|```", "", data).strip()  # Убираем кодовый блок и излишние пробелы/символы

        response_dict = json.loads(cleaned)

        print("json успешно распарсен:", response_dict)

        return response_dict

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("AIPIPE_TOKEN"),
    base_url=os.getenv("AIPIPE_BASE_URL", "https://aipipe.org/openrouter/v1")
)

print("Testing AIPipe connection...")

try:
    response = client.chat.completions.create(
        model="gpt-4o",  # Try this first
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print(f"✅ AIPipe works! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error with gpt-4o: {e}")
    print("\nTrying gpt-3.5-turbo instead...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print(f"✅ AIPipe works! Response: {response.choices[0].message.content}")
    except Exception as e2:
        print(f"❌ Error with gpt-3.5-turbo: {e2}")
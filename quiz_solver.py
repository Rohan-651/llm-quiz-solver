import time
import httpx
from playwright.async_api import async_playwright
from openai import AsyncOpenAI
import os
import json
from bs4 import BeautifulSoup

class QuizSolver:
    def __init__(self, email: str, secret: str):
        self.email = email
        self.secret = secret
        
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("AIPIPE_TOKEN"),
            base_url=os.getenv("AIPIPE_BASE_URL", "https://aipipe.org/openrouter/v1")
        )
        self.model = "gpt-4o"
        self.start_time = None
        
    async def solve_quiz_chain(self, initial_url: str):
        """Main function that solves a chain of quizzes"""
        current_url = initial_url
        self.start_time = time.time()
        
        print(f"\n🚀 Starting quiz chain at: {current_url}")
        
        question_num = 1
        while current_url and self._within_time_limit():
            print(f"\n📝 Question {question_num}: {current_url}")
            
            try:
                # Step 1: Get the quiz page content
                page_content = await self._fetch_page(current_url)
                print("✅ Fetched page content")
                
                # Step 2: Use LLM to understand the question
                question_data = await self._parse_question(page_content)
                print(f"✅ Parsed question: {question_data.get('question', '')[:100]}...")
                
                # Step 3: Solve the question
                answer = await self._solve_question(question_data)
                print(f"✅ Generated answer: {answer}")
                
                # Step 4: Submit the answer
                result = await self._submit_answer(
                    question_data.get('submit_url'),
                    current_url,
                    answer
                )
                
                # Step 5: Check if correct and get next URL
                if result.get('correct'):
                    print("✅ CORRECT!")
                    current_url = result.get('url')
                    question_num += 1
                else:
                    print(f"❌ WRONG: {result.get('reason')}")
                    current_url = result.get('url')
                    if not current_url:
                        print("No more URLs. Stopping.")
                        break
                        
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"\n🏁 Quiz completed! Solved {question_num} questions")
    
    async def _fetch_page(self, url: str) -> str:
        """Fetch a JavaScript-rendered page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            await browser.close()
            
            return content
    
    async def _parse_question(self, html_content: str) -> dict:
        """Extract question details from HTML using LLM"""
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        prompt = f"""
You are analyzing a quiz page. Extract the following information:

Page text:
{text[:3000]}

Links found: {links}

Return ONLY a JSON object with:
- "question": The actual question being asked
- "submit_url": URL where the answer should be submitted
- "data_urls": List of URLs to download data from (if any)
- "task_type": Type of task (calculation, scraping, visualization, etc.)

Return ONLY valid JSON, nothing else.
"""
        
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You extract structured data from text. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _solve_question(self, question_data: dict) -> any:
        """Use LLM to solve the question"""
        question = question_data.get('question', '')
        data_urls = question_data.get('data_urls', [])
        
        downloaded_data = []
        for url in data_urls[:3]:
            try:
                data = await self._download_file(url)
                downloaded_data.append(f"File from {url}: {data[:500]}")
            except:
                pass
        
        # Ask LLM to solve
        prompt = f"""
Question: {question}

Downloaded data: {downloaded_data}

Solve this question and provide ONLY the final answer.
- If it asks for a number, return just the number
- If it asks for text, return just the text
- If it asks for true/false, return just true or false
- Be concise, no explanation needed

Answer:"""
        
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You solve data analysis questions precisely."},
                {"role": "user", "content": prompt}
            ]
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        # Converting to appropriate type
        try:
            # Try number
            return float(answer_text.replace(',', ''))
        except:
            # Try boolean
            if answer_text.lower() in ['true', 'yes']:
                return True
            elif answer_text.lower() in ['false', 'no']:
                return False
            # Return as string
            return answer_text
    
    async def _download_file(self, url: str) -> str:
        """Download a file and return its content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            # If it's a PDF
            if 'pdf' in url.lower():
                return f"PDF file (binary data, {len(response.content)} bytes)"
            
            # Try to decode as text
            try:
                return response.text
            except:
                return f"Binary file ({len(response.content)} bytes)"
    
    async def _submit_answer(self, submit_url: str, quiz_url: str, answer: any):
        """Submit answer to evaluation endpoint"""
        payload = {
            "email": self.email,
            "secret": self.secret,
            "url": quiz_url,
            "answer": answer
        }
        
        print(f"📤 Submitting to: {submit_url}")
        print(f"📦 Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(submit_url, json=payload)
            result = response.json()
            print(f"📥 Response: {result}")
            return result
    
    def _within_time_limit(self) -> bool:
        """Check if still within 3 minute limit"""
        elapsed = time.time() - self.start_time
        remaining = 180 - elapsed
        print(f"⏱️  Time remaining: {remaining:.1f} seconds")
        return remaining > 0
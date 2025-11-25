import openai
import logging
from typing import List, Dict, Optional, Tuple
from app.core.config import settings
from app.models import AIGenerationLog
from sqlalchemy.orm import Session
import json
import re

logger = logging.getLogger(__name__)

class AIScraperAgent:
    """
    AI agent for generating web scraping scripts based on user requirements.
    Supports OpenAI GPT and other LLM providers.
    """
    
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    def generate_scraper_prompt(self, url: str, fields: List[str], description: str = None) -> str:
        """
        Generate a comprehensive prompt for the AI to create a scraper script.
        """
        prompt = f"""
You are an expert Python web scraping developer. Create a robust, production-ready web scraping script that:

1. Scrapes the data from: {url}
2. Extracts the following fields: {', '.join(fields)}
3. Handles errors gracefully
4. Includes proper rate limiting and anti-detection measures
5. Outputs data in JSON format

"""
        
        if description:
            prompt += f"Additional requirements: {description}\n"
            
        prompt += """
Requirements:
- Use BeautifulSoup4 for HTML parsing
- Include error handling and retries
- Add random delays between requests to avoid being blocked
- Use requests with proper headers (User-Agent, etc.)
- Include data validation
- Handle pagination if needed
- Return data as a list of dictionaries
- Use type hints
- Follow Python best practices
- Add logging

Please provide the complete Python script code only, without explanations.
"""
        
        return prompt
    
    async def generate_scraper_script(
        self, 
        url: str, 
        fields: List[str], 
        description: str = None,
        user_id: int = None,
        db: Session = None
    ) -> Tuple[str, Dict]:
        """
        Generate a web scraping script using AI.
        Returns tuple of (script_content, metadata)
        """
        try:
            prompt = self.generate_scraper_prompt(url, fields, description)
            
            # Use OpenAI if available, otherwise use a fallback template
            if self.openai_client:
                script, usage = await self._generate_with_openai(prompt)
            else:
                script = self._generate_template_script(url, fields, description)
                usage = {"model": "template", "tokens": 0, "cost": 0}
            
            # Log the generation attempt
            if db and user_id:
                await self._log_generation_attempt(db, user_id, prompt, script, usage)
            
            return script, usage
            
        except Exception as e:
            logger.error(f"Error generating scraper script: {e}")
            # Fallback to basic template
            fallback_script = self._generate_template_script(url, fields, description)
            return fallback_script, {"model": "fallback", "tokens": 0, "cost": 0, "error": str(e)}
    
    async def _generate_with_openai(self, prompt: str) -> Tuple[str, Dict]:
        """Generate script using OpenAI GPT"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert Python web scraping developer. Generate clean, production-ready code only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                stream=False
            )
            
            script_content = response.choices[0].message.content.strip()
            
            # Clean up the response to extract just the code
            script_content = self._extract_code_from_response(script_content)
            
            usage = {
                "model": settings.OPENAI_MODEL,
                "tokens": response.usage.total_tokens if response.usage else 0,
                "cost": self._calculate_cost(response.usage.total_tokens if response.usage else 0)
            }
            
            return script_content, usage
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from AI response"""
        # Remove code blocks if present
        if response.startswith("```python"):
            response = response.replace("```python", "", 1)
        elif response.startswith("```"):
            response = response.replace("```", "", 1)
        
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_template_script(self, url: str, fields: List[str], description: str = None) -> str:
        """
        Generate a basic template script when AI is not available.
        """
        fields_str = ", ".join([f'"{field}"' for field in fields])
        
        script = f'''
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """Template web scraper for {url}"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({{
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }})
        self.fields = [{fields_str}]
        
    def scrape_data(self, url: str) -> List[Dict[str, Any]]:
        """Main scraping method"""
        try:
            logger.info(f"Starting scrape for {{url}}")
            
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Customize this selector based on the website structure
            items = soup.find_all('div', class_='item')  # Example selector
            
            results = []
            for item in items:
                data = {{}}
                for field in self.fields:
                    # Customize these selectors based on your needs
                    element = item.find(class_=f'{{field}}')
                    if element:
                        data[field] = element.get_text(strip=True)
                    else:
                        data[field] = None
                
                if any(data.values()):  # Only add if we have some data
                    results.append(data)
            
            logger.info(f"Scraped {{len(results)}} items")
            return results
            
        except Exception as e:
            logger.error(f"Error during scraping: {{e}}")
            return []

def main():
    """Main function"""
    scraper = WebScraper()
    url = "{url}"
    
    try:
        data = scraper.scrape_data(url)
        
        # Output as JSON
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Save to file
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Scraping failed: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
        
        return script.strip()
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate approximate cost based on token usage"""
        # Rough estimation based on OpenAI pricing (adjust as needed)
        cost_per_token = 0.000002  # $2 per 1M tokens for GPT-3.5-turbo
        return tokens * cost_per_token
    
    async def _log_generation_attempt(
        self, 
        db: Session, 
        user_id: int, 
        prompt: str, 
        script: str, 
        usage: Dict
    ):
        """Log AI generation attempts for tracking and billing"""
        try:
            log_entry = AIGenerationLog(
                user_id=user_id,
                prompt=prompt[:1000],  # Truncate for storage
                generated_script=script[:10000],  # Truncate for storage
                ai_model_used=usage.get("model", "unknown"),
                tokens_used=usage.get("tokens", 0),
                cost=usage.get("cost", 0.0),
                success=usage.get("error") is None,
                error_message=usage.get("error")
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log AI generation attempt: {e}")
            db.rollback()
    
    def validate_script(self, script: str) -> Tuple[bool, List[str]]:
        """
        Validate the generated Python script for basic syntax and security issues.
        Returns (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Compile the script to check for syntax errors
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax error: {{e.msg}} at line {{e.lineno}}")
            return False, issues
        
        # Check for potentially dangerous imports
        dangerous_imports = ['subprocess', 'os.system', 'eval', 'exec(']
        for dangerous in dangerous_imports:
            if dangerous in script:
                issues.append(f"Potentially dangerous code detected: {{dangerous}}")
        
        # Check script length
        if len(script) > settings.MAX_SCRIPT_SIZE:
            issues.append(f"Script too long ({{len(script)}} > {{settings.MAX_SCRIPT_SIZE}} characters)")
        
        # Check for common security patterns
        security_patterns = [
            r'import\s+os\.',
            r'__import__',
            r'compile\(',
            r'file\s*\(',
            r'open\s*\(',
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, script):
                issues.append(f"Security concern: pattern '{{pattern}}' detected")
        
        return len(issues) == 0, issues
import requests
import json
import urllib.parse
import re
import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from news.models import Article, Category, District
from google import genai 
from dotenv import load_dotenv

# Load the secrets from your .env file
load_dotenv()

# Get the API key securely from the environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class Command(BaseCommand):
    help = 'Worker script that fetches and writes the news article.'

    def add_arguments(self, parser):
        parser.add_argument('topic', type=str, help='Topic to search for')

    def handle(self, *args, **options):
        # Double check that the API key was actually loaded
        if not GEMINI_API_KEY:
            self.stdout.write(self.style.ERROR("   ❌ Error: GEMINI_API_KEY not found. Make sure your .env file is set up correctly."))
            return

        topic = options['topic']
        self.stdout.write(f"🔍 Worker Searching on Google News: {topic}...")

        try:
            query = urllib.parse.quote(f"{topic}")
            url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
            
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')

            if not items:
                self.stdout.write(self.style.WARNING("   ⚠️ No recent news found on Google. Skipping cycle."))
                return
            
            results = []
            for item in items[:5]:
                results.append({
                    'title': item.title.text,
                    'href': item.link.text
                })
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Search Engine Error: {e}. Skipping cycle."))
            return
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        processed_count = 0
        
        for result in results:
            if processed_count >= 1: break 

            url = result['href']
            title = result['title']

            if Article.objects.filter(source_url=url).exists():
                self.stdout.write(self.style.WARNING(f"   Skipping (Duplicate): {title}"))
                continue
            
            try:
                content_data = self.fetch_page_content(url)
                if not content_data: 
                    continue
                
                # Unpack the 3 variables returned by the updated function
                raw_text, extracted_image_url, real_url = content_data
                
                # Check if we got enough text to work with
                if len(raw_text) < 400:
                    self.stdout.write(f"   Skipping (Content too short: {len(raw_text)} chars)")
                    continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   Fetch Error: {e}"))
                continue

            self.stdout.write("   🤖 RraSHI AI is writing...")
            
            prompt = f"""
            You are "RraSHI AI", a senior editor for "Tripura Now".
            Rewrite the text below into a professional news article.

            RULES:
            1. CATEGORY: ONE of ["Tripura", "Northeast", "India", "Global", "Others"]
            2. DISTRICT: If Tripura, pick one from ["West Tripura", "Sepahijala", "Gomati", "South Tripura", "Khowai", "Dhalai", "Unakoti", "North Tripura"]. Else null.
            3. FORMAT: You MUST respond ONLY with a valid JSON object using exactly these lowercase keys:
            {{"title": "...", "subtitle": "...", "body": "...", "category": "...", "district": "..."}}

            RAW TEXT:
            {raw_text[:4500]}...
            """
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                clean_json = response.text.strip()
                if clean_json.startswith('```json'):
                    clean_json = clean_json[7:]
                if clean_json.endswith('```'):
                    clean_json = clean_json[:-3]
                    
                data = json.loads(clean_json.strip())
                
                # Check if the AI actually returned the expected format
                if not isinstance(data, dict):
                    raise ValueError("AI did not return a dictionary object.")
                
                # Safely get fields, checking for both lower and uppercase keys
                final_title = data.get('title') or data.get('Title')
                
                if not final_title:
                    # Print the AI's output so you can see exactly why it failed
                    self.stdout.write(self.style.ERROR(f"   ❌ AI output was: {clean_json[:200]}..."))
                    raise ValueError("AI response missing 'title' field.")
                
                # Make sure these fields exist in the data dictionary before saving
                data['title'] = final_title
                data['subtitle'] = data.get('subtitle') or data.get('Subtitle') or ''
                data['body'] = data.get('body') or data.get('Body') or ''
                
                cat = data.get('category') or data.get('Category') or 'Others'
                data['category'] = cat
                
                dist = data.get('district') or data.get('District')
                data['district'] = dist
                
                # Save using the resolved real_url
                self.save_article(data, real_url, extracted_image_url)
                
                self.stdout.write(self.style.SUCCESS(f"   ✅ Published by RraSHI AI: {final_title}"))
                processed_count += 1

            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(f"   ❌ JSON Parsing Error. AI output was: {clean_json[:100]}..."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ AI/Save Error: {e}"))

    def fetch_page_content(self, url):
        self.stdout.write(f"   🔗 Following Link -> {url[:60]}...")
        
        try:
            # 1. Let requests follow the Google News redirect naturally
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            redirect_resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            real_url = redirect_resp.url  # This is the actual news site URL!
            self.stdout.write(f"   📍 Target URL -> {real_url[:60]}...")

            # 2. Extract the Image using BeautifulSoup
            image_url = None
            soup = BeautifulSoup(redirect_resp.text, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image: 
                image_url = og_image.get("content")
            if not image_url:
                tw_image = soup.find("meta", name="twitter:image")
                if tw_image: 
                    image_url = tw_image.get("content")

            # 3. 🚀 THE MAGIC TRICK: Use Jina Reader to get the text for the AI
            # This bypasses paywalls, JS blocks, and extracts pure article text.
            jina_url = f"https://r.jina.ai/{real_url}"
            jina_resp = requests.get(jina_url, timeout=25)
            
            raw_text = jina_resp.text

            # Return the text, image, and the real URL
            return raw_text, image_url, real_url
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Scraping Error: {e}"))
            return None

    def save_article(self, data, source_url, extracted_image_url):
        cat_name = data.get('category', 'Others').capitalize()
        valid_cats = ["Tripura", "Northeast", "India", "Global", "Others"]
        if cat_name not in valid_cats: cat_name = "Others"
        
        category, _ = Category.objects.get_or_create(name=cat_name)
        
        district_obj = None
        if cat_name == "Tripura":
            dist_name = data.get('district')
            if dist_name:
                district_obj, _ = District.objects.get_or_create(name=dist_name)
            else:
                district_obj, _ = District.objects.get_or_create(name="West Tripura")

        final_image = extracted_image_url if extracted_image_url else "https://picsum.photos/seed/news/800/600"

        Article.objects.create(
            title=data['title'],
            subtitle=data['subtitle'],
            content=data['body'],
            category=category,
            district=district_obj,
            source_url=source_url,
            image_url=final_image,
            author="RraSHI AI", 
            is_breaking=True,
            is_trending=True
        )
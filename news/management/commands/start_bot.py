import time
import random
import datetime
from django.utils import timezone
from django.core.management import call_command
from django.core.management.base import BaseCommand
from news.models import Article 

class Command(BaseCommand):
    help = 'Starts RaShi AI with Ultimate Priority Mode'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 RaShi AI Ultimate Auto-Pilot Started"))
        self.stdout.write("Strategy: 50% Tripura | 20% NE | 15% India | 10% Global | 5% Others")

        # MASTER TOPIC DATABASE
        TOPIC_GROUPS = {
            "TRIPURA": [
                "Tripura Public Service Commission (TPSC) latest notification 2026",
                "JRBT Tripura interview result updates",
                "Tripura Police recruitment rally dates 2026",
                "Tripura TET exam date verification",
                "TBSE Madhyamik HS exam routine 2026",
                "Tripura University admission news",
                "Agartala Municipal Corporation news",
                "West Tripura district administration updates",
                "Sepahijala district magistrate office news",
                "Tripura Sundari Temple news",
                "Dhalai district development news",
                "Tripura CM Manik Saha latest announcements",
                "Tipra Motha party latest news",
                "Petrol Diesel price Agartala",
                "MBB Airport Agartala flight news",
                "TSECL Tripura power cut schedule"
            ],
            "NORTHEAST": [
                "Assam-Tripura national highway condition",
                "Meghalaya tourism news",
                "Mizoram border trade updates",
                "Manipur latest news",
                "Northeast Frontier Railway train schedule"
            ],
            "INDIA": [
                "PM Modi latest announcements",
                "Central Government schemes India",
                "Indian stock market updates",
                "Supreme Court India judgments",
                "Indian Railways news"
            ],
            "GLOBAL": [
                "Global AI technology trends",
                "WHO health alerts",
                "India Bangladesh relations news",
                "Space exploration ISRO NASA"
            ],
            "OTHERS": [
                "Best 5G smartphones India",
                "Indian Cricket Team schedule",
                "ISL Football news",
                "Health tips for students"
            ]
        }

        while True:
            # 1. PRIORITY SELECTION
            categories = ["TRIPURA", "NORTHEAST", "INDIA", "GLOBAL", "OTHERS"]
            weights = [50, 20, 15, 10, 5]
            
            chosen_category = random.choices(categories, weights=weights, k=1)[0]
            candidate_topic = random.choice(TOPIC_GROUPS[chosen_category])

            # 2. DUPLICATE CHECK
            if self.has_posted_recently(candidate_topic):
                self.stdout.write(self.style.WARNING(f"🚫 [SKIP] Recent: {candidate_topic}"))
                time.sleep(2) 
                continue 

            # 3. RUN THE BOT
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- 🎯 SELECTED: {chosen_category} ({candidate_topic}) ---"))
            
            try:
                call_command('run_rashi', topic=candidate_topic)
                
                # Sleep between 20 to 40 minutes
                wait_minutes = random.randint(20, 40)
                self.stdout.write(f"😴 Sleeping for {wait_minutes} minutes...")
                time.sleep(wait_minutes * 60)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Cycle Error: {e}"))
                time.sleep(60)

    def has_posted_recently(self, topic_keyword):
        # Time threshold: 24 hours
        time_threshold = timezone.now() - datetime.timedelta(hours=24)
        
        # Simple cleanup to find core topic matches
        clean_term = topic_keyword.replace("latest news", "").replace("updates", "").replace("2026", "").strip()
        
        # Check database
        exists = Article.objects.filter(
            created_at__gte=time_threshold,
            title__icontains=clean_term
        ).exists()

        return exists
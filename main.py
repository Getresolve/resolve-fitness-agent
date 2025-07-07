#!/usr/bin/env python3
"""
Resolve Fitness Lead Generation Agent (Optimized for Render.com)
Auto-finds and engages potential gym members in Kanagawa, Japan
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict
import aiohttp

# Configuration for low-cost operation
MAX_LEADS_PER_DAY = 20  # Stay under free tier limits
MIN_SECONDS_BETWEEN_REQUESTS = 30  # Avoid rate limiting
REQUEST_TIMEOUT = 30  # Seconds before timeout
DATA_RETENTION_DAYS = 30  # Keep leads for 30 days

# Configure efficient logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Optimized lead data structure"""
    name: str
    platform: str
    profile_url: str
    content: str
    location: str
    score: int
    contact_method: str
    status: str = "new"
    created_at: str = datetime.now().isoformat()
    last_contact: str = ""

class ResolveLeadAgent:
    """Optimized lead generation agent for Render.com free tier"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.leads_file = self.data_dir / "leads.json"
        self.config_file = self.data_dir / "config.json"
        self.leads: List[Lead] = []
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT))
        self.config = self._load_config()
        
    def __del__(self):
        asyncio.get_event_loop().run_until_complete(self.session.close())
    
    def _load_config(self) -> Dict:
        """Load configuration with memory-efficient defaults"""
        default_config = {
            "target_keywords": ["gym", "fitness", "workout"],
            "target_locations": ["kanagawa"],
            "target_platforms": {
                "reddit": ["r/japanlife"],
                "facebook": ["Tokyo Expat Network"]
            },
            "messaging_templates": {
                "reddit_comment": "Hey! Check out Resolve Fitness in Kanagawa...",
                "facebook_message": "Hi {name}! Saw your post about fitness..."
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
            return default_config
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            return default_config
    
    def _clean_old_leads(self):
        """Remove leads older than retention period"""
        cutoff = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
        self.leads = [
            lead for lead in self.leads 
            if datetime.fromisoformat(lead.created_at) > cutoff
        ]
    
    async def _save_data(self):
        """Efficient data saving with rotation"""
        try:
            self._clean_old_leads()
            with open(self.leads_file, 'w') as f:
                json.dump([asdict(lead) for lead in self.leads[:1000]], f)  # Limit to 1000 leads
        except Exception as e:
            logger.error(f"Save failed: {e}")

    async def scrape_platform(self, platform: str) -> List[Lead]:
        """Generic platform scraper with rate limiting"""
        logger.info(f"Scraping {platform}")
        await asyncio.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
        
        # Simulated response to avoid API costs
        return [Lead(
            name=f"Test_User_{platform}",
            platform=platform,
            profile_url=f"https://{platform}.com/test",
            content=f"Looking for gym in Kanagawa",
            location="kanagawa",
            score=10,
            contact_method=f"{platform}_message"
        )]
    
    async def send_message(self, lead: Lead) -> bool:
        """Mock message sender to avoid actual API calls"""
        logger.info(f"Would send to {lead.name} via {lead.platform}")
        lead.status = "contacted"
        lead.last_contact = datetime.now().isoformat()
        return True
    
    async def run_daily_cycle(self):
        """Optimized daily cycle for Render.com"""
        try:
            # Load existing data
            if self.leads_file.exists():
                with open(self.leads_file, 'r') as f:
                    self.leads = [Lead(**lead) for lead in json.load(f)]
            
            # Scrape platforms
            tasks = [
                self.scrape_platform("reddit"),
                self.scrape_platform("facebook")
            ]
            results = await asyncio.gather(*tasks)
            
            # Process new leads
            new_leads = [
                lead for platform_leads in results 
                for lead in platform_leads 
                if lead.profile_url not in {l.profile_url for l in self.leads}
            ][:MAX_LEADS_PER_DAY]
            
            self.leads.extend(new_leads)
            
            # Contact high priority leads
            high_priority = [l for l in new_leads if l.score >= 15][:5]  # Limit to 5/day
            for lead in high_priority:
                await self.send_message(lead)
                await asyncio.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
            
            # Save data
            await self._save_data()
            
            return {
                "status": "success",
                "new_leads": len(new_leads),
                "contacted": len(high_priority)
            }
        except Exception as e:
            logger.error(f"Daily cycle failed: {e}")
            return {"status": "error", "error": str(e)}

async def main():
    """Optimized main function"""
    agent = ResolveLeadAgent()
    report = await agent.run_daily_cycle()
    
    print(f"\nDaily Report: {json.dumps(report, indent=2)}")
    logger.info(f"Cycle completed: {report}")

if __name__ == "__main__":
    asyncio.run(main())

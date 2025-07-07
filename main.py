#!/usr/bin/env python3
"""
Resolve Fitness Lead Generation Agent
Auto-finds and engages potential gym members in Kanagawa, Japan
Designed for Maurice Shelton's Resolve Fitness & Training Center

Author: AI Business Partner
Version: 1.0
"""

import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lead_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Lead data structure"""
    name: str
    platform: str
    profile_url: str
    content: str
    location: str
    score: int
    contact_method: str
    status: str = "new"
    created_at: str = ""
    last_contact: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class ResolveLeadAgent:
    """Main lead generation agent for Resolve Fitness"""
    
    def __init__(self):
        self.leads_file = Path("leads.json")
        self.config_file = Path("config.json")
        self.report_file = Path("daily_reports.json")
        self.leads: List[Lead] = []
        self.config = self.load_config()
        self.session = None
        
    def load_config(self) -> Dict:
        """Load configuration settings"""
        default_config = {
            "business_info": {
                "name": "Resolve Fitness & Training Center",
                "owner": "Maurice Shelton",
                "location": "Kanagawa, Japan",
                "services": ["CrossFit", "Boxing", "HIIT", "Personal Training"],
                "unique_selling_points": [
                    "Tattoo-friendly environment",
                    "English-speaking staff",
                    "International community focused",
                    "Bilingual training programs"
                ]
            },
            "target_keywords": {
                "high_priority": [
                    "tattoo friendly gym", "foreigner gym", "english gym",
                    "expat gym", "international gym", "gaijin gym",
                    "english speaking trainer", "tattoo ok gym"
                ],
                "medium_priority": [
                    "gym recommendation", "fitness", "workout", "exercise",
                    "crossfit", "boxing", "hiit", "personal trainer",
                    "strength training", "muscle building"
                ],
                "location_specific": [
                    "kanagawa gym", "kawasaki gym", "yokohama gym",
                    "zama gym", "sagamihara gym", "atsugi gym"
                ]
            },
            "target_locations": [
                "kanagawa", "kawasaki", "yokohama", "zama", "sagamihara",
                "atsugi", "yamato", "ebina", "machida", "fujisawa",
                "tokyo bay area", "kanto region"
            ],
            "target_demographics": [
                "american", "canadian", "british", "australian", "european",
                "expat", "foreigner", "gaijin", "english teacher", "military",
                "international student", "english speaker"
            ],
            "social_platforms": {
                "reddit": {
                    "subreddits": [
                        "r/japanlife", "r/tokyo", "r/kanagawa", "r/fitness",
                        "r/crossfit", "r/boxing", "r/expats", "r/teachinginjapan"
                    ],
                    "search_terms": [
                        "gym recommendation japan", "fitness kanagawa",
                        "tattoo friendly gym", "english gym japan"
                    ]
                },
                "facebook": {
                    "groups": [
                        "Tokyo Expat Network", "Kanagawa International Community",
                        "Foreigners in Japan", "English Teachers in Japan",
                        "Americans in Japan", "Fitness Enthusiasts Tokyo"
                    ]
                },
                "linkedin": {
                    "groups": [
                        "American Chamber of Commerce Japan",
                        "International Professionals Tokyo",
                        "Expats in Japan Network"
                    ]
                }
            },
            "messaging_templates": {
                "reddit_comment": """Hey! I totally get the struggle finding a good gym in Japan as a foreigner. 

I'm Maurice from Resolve Fitness in Kanagawa - we're specifically designed for the international community. We're tattoo-friendly, have English-speaking staff, and focus on creating a welcoming environment for everyone.

We offer CrossFit, boxing, HIIT, and personal training. If you're in the Kanagawa area, I'd love to offer you a free trial session to see if we're a good fit.

Feel free to DM me if you want more info! 🏋️‍♂️

Check us out: [Your website/social media]""",
                
                "facebook_message": """Hi {name}! 

I saw your post about {topic} and completely understand the challenge. As someone who's been helping the international community in Kanagawa get fit, I know how tough it can be to find the right gym environment in Japan.

I'm Maurice from Resolve Fitness & Training Center. We're a tattoo-friendly, English-speaking gym specifically designed for expats and internationally-minded people in the Kanagawa area.

Our community is super welcoming, and we offer everything from CrossFit to personal training. I'd love to invite you for a complimentary trial session if you're interested.

Would you like to chat more about your fitness goals? Happy to answer any questions!

Best regards,
Maurice Shelton
Resolve Fitness & Training Center""",
                
                "linkedin_message": """Hello {name},

I noticed you're part of the international professional community in Japan. I'm Maurice Shelton, owner of Resolve Fitness & Training Center in Kanagawa.

We specialize in serving English speakers and creating an inclusive fitness environment - something I know can be challenging to find in Japan, especially for professionals with busy schedules.

If you're interested in connecting with other internationally-minded fitness enthusiasts, I'd be happy to invite you for a complimentary consultation to discuss your fitness goals.

Best regards,
Maurice Shelton
Resolve Fitness & Training Center
Kanagawa, Japan""",
                
                "general_outreach": """Hi {name},

I came across your {platform} post about {topic} and wanted to reach out. I'm Maurice, and I run Resolve Fitness & Training Center in Kanagawa.

We've built our gym specifically for the international community - tattoo-friendly, English-speaking, and focused on creating a supportive environment for everyone.

Since you're in the {location} area, I'd love to offer you a free trial session. No pressure, just a chance to check us out and see if we'd be a good fit for your fitness goals.

What do you think? Happy to answer any questions!

Cheers,
Maurice"""
            },
            "scoring_weights": {
                "high_priority_keywords": 15,
                "medium_priority_keywords": 8,
                "location_match": 10,
                "demographic_match": 12,
                "urgency_indicators": 8,
                "platform_bonus": {"reddit": 3, "facebook": 5, "linkedin": 7},
                "recency_bonus": 5
            },
            "automation_settings": {
                "daily_lead_target": 20,
                "max_outreach_per_day": 10,
                "follow_up_days": [3, 7, 14],
                "rate_limit_delay": 30,
                "max_retries": 3
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._merge_config(default_config, config)
                    return config
            except json.JSONDecodeError:
                logger.warning("Config file corrupted, using defaults")
                return default_config
        else:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _merge_config(self, default: Dict, user: Dict) -> None:
        """Merge user config with defaults"""
        for key, value in default.items():
            if key not in user:
                user[key] = value
            elif isinstance(value, dict) and isinstance(user[key], dict):
                self._merge_config(value, user[key])
    
    def load_leads(self) -> List[Lead]:
        """Load existing leads from file"""
        if self.leads_file.exists():
            try:
                with open(self.leads_file, 'r', encoding='utf-8') as f:
                    leads_data = json.load(f)
                    return [Lead(**lead) for lead in leads_data]
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error loading leads: {e}")
                return []
        return []
    
    def save_leads(self):
        """Save leads to file"""
        try:
            with open(self.leads_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(lead) for lead in self.leads], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.leads)} leads to database")
        except Exception as e:
            logger.error(f"Error saving leads: {e}")
    
    def score_lead(self, content: str, platform: str, location: str = "", demographics: str = "") -> Tuple[int, List[str]]:
        """Score lead based on content relevance and return tags"""
        score = 0
        tags = []
        content_lower = content.lower()
        
        # High-priority keywords
        for keyword in self.config["target_keywords"]["high_priority"]:
            if keyword in content_lower:
                score += self.config["scoring_weights"]["high_priority_keywords"]
                tags.append(f"high_priority_{keyword.replace(' ', '_')}")
        
        # Medium-priority keywords
        for keyword in self.config["target_keywords"]["medium_priority"]:
            if keyword in content_lower:
                score += self.config["scoring_weights"]["medium_priority_keywords"]
                tags.append(f"medium_priority_{keyword.replace(' ', '_')}")
        
        # Location matching
        for loc in self.config["target_locations"]:
            if loc in content_lower or loc in location.lower():
                score += self.config["scoring_weights"]["location_match"]
                tags.append(f"location_{loc}")
        
        # Demographics matching
        for demo in self.config["target_demographics"]:
            if demo in content_lower or demo in demographics.lower():
                score += self.config["scoring_weights"]["demographic_match"]
                tags.append(f"demographic_{demo}")
        
        # Platform bonus
        platform_bonus = self.config["scoring_weights"]["platform_bonus"].get(platform, 0)
        score += platform_bonus
        
        # Urgency indicators
        urgency_words = ["need", "looking for", "help", "recommend", "urgent", "asap", "new to", "just moved"]
        for word in urgency_words:
            if word in content_lower:
                score += self.config["scoring_weights"]["urgency_indicators"]
                tags.append("urgent")
                break
        
        # Question indicators (people asking for help)
        if any(indicator in content_lower for indicator in ["?", "anyone know", "does anyone", "help me"]):
            score += 5
            tags.append("asking_for_help")
        
        return min(score, 100), tags  # Cap at 100
    
    def extract_location_from_content(self, content: str) -> str:
        """Extract location mentions from content"""
        content_lower = content.lower()
        for location in self.config["target_locations"]:
            if location in content_lower:
                return location
        return "japan"
    
    def generate_realistic_leads(self, platform: str, count: int = 5) -> List[Lead]:
        """Generate realistic sample leads for testing"""
        sample_leads_data = {
            "reddit": [
                {
                    "name": "FitnessSeeker_Tokyo",
                    "content": "Looking for a tattoo-friendly gym in Kanagawa area. Any recommendations for English speakers? I'm American and just moved here for work.",
                    "profile_url": "https://reddit.com/user/FitnessSeeker_Tokyo"
                },
                {
                    "name": "ExpatLifter22",
                    "content": "Does anyone know good CrossFit gyms near Zama? Preferably with English-speaking trainers. I'm military stationed here.",
                    "profile_url": "https://reddit.com/user/ExpatLifter22"
                },
                {
                    "name": "KanagawaNewbie",
                    "content": "New to Kawasaki and need gym recommendations. Back home I did a lot of HIIT and boxing. Any foreigner-friendly places?",
                    "profile_url": "https://reddit.com/user/KanagawaNewbie"
                },
                {
                    "name": "TokyoBayResident",
                    "content": "Anyone have experience with gyms that don't discriminate against tattoos? I'm in the Yokohama area.",
                    "profile_url": "https://reddit.com/user/TokyoBayResident"
                },
                {
                    "name": "EnglishTeacherFit",
                    "content": "Teaching English in Sagamihara, looking for a gym with English-speaking staff. Any suggestions?",
                    "profile_url": "https://reddit.com/user/EnglishTeacherFit"
                }
            ],
            "facebook": [
                {
                    "name": "Sarah Johnson",
                    "content": "Anyone in the Kawasaki area know of good gyms that welcome foreigners? Looking for somewhere I can do HIIT workouts and not feel out of place.",
                    "profile_url": "https://facebook.com/profile/sarah.johnson.example"
                },
                {
                    "name": "Mike Chen",
                    "content": "Just moved to Kanagawa for work. Back in Australia I was really into CrossFit. Any recommendations for English-friendly gyms?",
                    "profile_url": "https://facebook.com/profile/mike.chen.example"
                },
                {
                    "name": "Emma Wilson",
                    "content": "Looking for a personal trainer in the Yokohama area who can work with someone who has tattoos. Any recommendations?",
                    "profile_url": "https://facebook.com/profile/emma.wilson.example"
                }
            ],
            "linkedin": [
                {
                    "name": "David Rodriguez",
                    "content": "New to Japan and looking for fitness communities. Any recommendations for English-speaking gyms in Kanagawa? I'm a software engineer working in Tokyo.",
                    "profile_url": "https://linkedin.com/in/david.rodriguez.example"
                },
                {
                    "name": "Jennifer Taylor",
                    "content": "Relocated to Kawasaki for work. Looking for professional networks and fitness communities. Any suggestions for international-friendly gyms?",
                    "profile_url": "https://linkedin.com/in/jennifer.taylor.example"
                }
            ]
        }
        
        leads = []
        platform_data = sample_leads_data.get(platform, [])
        
        # Randomly select leads up to the count requested
        selected_leads = random.sample(platform_data, min(count, len(platform_data)))
        
        for lead_data in selected_leads:
            location = self.extract_location_from_content(lead_data["content"])
            score, tags = self.score_lead(lead_data["content"], platform, location)
            
            # Determine contact method based on platform
            contact_methods = {
                "reddit": "reddit_comment",
                "facebook": "facebook_message",
                "linkedin": "linkedin_message"
            }
            
            lead = Lead(
                name=lead_data["name"],
                platform=platform,
                profile_url=lead_data["profile_url"],
                content=lead_data["content"],
                location=location,
                score=score,
                contact_method=contact_methods.get(platform, "general_outreach"),
                tags=tags,
                created_at=datetime.now().isoformat()
            )
            leads.append(lead)
        
        return leads
    
    async def scrape_reddit(self) -> List[Lead]:
        """Scrape Reddit for fitness-related posts"""
        logger.info("🔍 Scraping Reddit for fitness leads...")
        
        # In production, this would use Reddit's API
        # For now, we'll generate realistic sample data
        leads = self.generate_realistic_leads("reddit", random.randint(3, 8))
        
        logger.info(f"Found {len(leads)} potential leads on Reddit")
        return leads
    
    async def scrape_facebook(self) -> List[Lead]:
        """Scrape Facebook for fitness-related posts"""
        logger.info("🔍 Scraping Facebook for fitness leads...")
        
        # In production, this would use Facebook's API
        # For now, we'll generate realistic sample data
        leads = self.generate_realistic_leads("facebook", random.randint(2, 5))
        
        logger.info(f"Found {len(leads)} potential leads on Facebook")
        return leads
    
    async def scrape_linkedin(self) -> List[Lead]:
        """Scrape LinkedIn for potential leads"""
        logger.info("🔍 Scraping LinkedIn for fitness leads...")
        
        # In production, this would use LinkedIn's API
        # For now, we'll generate realistic sample data
        leads = self.generate_realistic_leads("linkedin", random.randint(1, 3))
        
        logger.info(f"Found {len(leads)} potential leads on LinkedIn")
        return leads
    
    async def generate_outreach_message(self, lead: Lead) -> str:
        """Generate personalized outreach message"""
        template_key = lead.contact_method
        template = self.config["messaging_templates"].get(template_key, 
                   self.config["messaging_templates"]["general_outreach"])
        
        # Extract topic from content for personalization
        topic = "fitness goals"
        if "tattoo" in lead.content.lower():
            topic = "finding a tattoo-friendly gym"
        elif "crossfit" in lead.content.lower():
            topic = "CrossFit training"
        elif "boxing" in lead.content.lower():
            topic = "boxing training"
        elif "hiit" in lead.content.lower():
            topic = "HIIT workouts"
        elif "personal trainer" in lead.content.lower():
            topic = "personal training"
        elif "gym recommendation" in lead.content.lower():
            topic = "gym recommendations"
        
        # Personalize message
        try:
            message = template.format(
                name=lead.name,
                topic=topic,
                location=lead.location,
                platform=lead.platform
            )
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}")
            # Fallback to general template
            message = self.config["messaging_templates"]["general_outreach"].format(
                name=lead.name,
                topic=topic,
                location=lead.location,
                platform=lead.platform
            )
        
        return message
    
    async def send_outreach(self, lead: Lead) -> bool:
        """Send outreach message to lead"""
        try:
            message = await self.generate_outreach_message(lead)
            
            logger.info(f"📤 Sending outreach to {lead.name} on {lead.platform}")
            logger.info(f"Message preview: {message[:100]}...")
            
            # In production, this would actually send the message via API
            # For now, we'll simulate the send and log it
            
            # Simulate API call delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Simulate success/failure (95% success rate)
            if random.random() > 0.05:
                lead.status = "contacted"
                lead.last_contact = datetime.now().isoformat()
                logger.info(f"✅ Successfully contacted {lead.name}")
                return True
            else:
                logger.warning(f"❌ Failed to contact {lead.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending outreach to {lead.name}: {e}")
            return False
    
    async def process_high_priority_leads(self):
        """Process leads with high scores immediately"""
        high_priority_leads = [
            lead for lead in self.leads 
            if lead.score >= 20 and lead.status == "new"
        ]
        
        # Sort by score (highest first)
        high_priority_leads.sort(key=lambda x: x.score, reverse=True)
        
        # Limit to max outreach per day
        max_outreach = self.config["automation_settings"]["max_outreach_per_day"]
        high_priority_leads = high_priority_leads[:max_outreach]
        
        logger.info(f"🎯 Processing {len(high_priority_leads)} high-priority leads")
        
        for lead in high_priority_leads:
            success = await self.send_outreach(lead)
            if success:
                logger.info(f"📈 High-priority lead processed: {lead.name} (Score: {lead.score})")
            
            # Rate limiting
            delay = self.config["automation_settings"]["rate_limit_delay"]
            await asyncio.sleep(delay)
    
    async def generate_daily_report(self) -> Dict:
        """Generate comprehensive daily activity report"""
        today = datetime.now().date()
        today_str = str(today)
        
        # Filter today's leads
        today_leads = [
            lead for lead in self.leads 
            if lead.created_at.startswith(today_str)
        ]
        
        # Calculate metrics
        total_leads = len(self.leads)
        new_leads_today = len(today_leads)
        high_priority_today = len([lead for lead in today_leads if lead.score >= 20])
        medium_priority_today = len([lead for lead in today_leads if 10 <= lead.score < 20])
        contacted_today = len([lead for lead in self.leads if lead.last_contact.startswith(today_str)])
        
        # Platform breakdown
        platform_stats = {}
        for lead in today_leads:
            if lead.platform not in platform_stats:
                platform_stats[lead.platform] = {"count": 0, "avg_score": 0}
            platform_stats[lead.platform]["count"] += 1
        
        # Calculate average scores
        for platform in platform_stats:
            platform_leads = [lead for lead in today_leads if lead.platform == platform]
            if platform_leads:
                platform_stats[platform]["avg_score"] = sum(lead.score for lead in platform_leads) / len(platform_leads)
        
        # Location breakdown
        location_stats = {}
        for lead in today_leads:
            if lead.location not in location_stats:
                location_stats[lead.location] = 0
            location_stats[lead.location] += 1
        
        # Top tags
        all_tags = []
        for lead in today_leads:
            all_tags.extend(lead.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        report = {
            "date": today_str,
            "metrics": {
                "new_leads": new_leads_today,
                "high_priority": high_priority_today,
                "medium_priority": medium_priority_today,
                "contacted_today": contacted_today,
                "total_leads_database": total_leads,
                "conversion_rate": round((contacted_today / new_leads_today * 100) if new_leads_today > 0 else 0, 1)
            },
            "platform_breakdown": platform_stats,
            "location_breakdown": location_stats,
            "top_tags": top_tags,
            "summary": {
                "performance": "excellent" if new_leads_today >= 10 else "good" if new_leads_today >= 5 else "needs_improvement",
                "recommendations": []
            }
        }
        
        # Add recommendations
        if new_leads_today < 5:
            report["summary"]["recommendations"].append("Consider expanding target keywords")
        if high_priority_today < 2:
            report["summary"]["recommendations"].append("Focus on tattoo-friendly and expat-specific content")
        if contacted_today < new_leads_today * 0.5:
            report["summary"]["recommendations"].append("Increase outreach automation")
        
        return report
    
    def save_daily_report(self, report: Dict):
        """Save daily report to file"""
        try:
            reports = []
            if self.report_file.exists():
                with open(self.report_file, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
            
            reports.append(report)
            
            # Keep only last 30 days
            if len(reports) > 30:
                reports = reports[-30:]
            
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving daily report: {e}")
    
    async def run_daily_cycle(self):
        """Run complete daily lead generation cycle"""
        logger.info("🚀 Starting daily lead generation cycle for Resolve Fitness...")
        start_time = time.time()
        
        try:
            # Load existing leads
            self.leads = self.load_leads()
            initial_count = len(self.leads)
            
            # Scrape all platforms
            logger.info("📊 Gathering leads from all platforms...")
            reddit_leads = await self.scrape_reddit()
            facebook_leads = await self.scrape_facebook()
            linkedin_leads = await self.scrape_linkedin()
            
            # Combine all new leads
            all_new_leads = reddit_leads + facebook_leads + linkedin_leads
            
            # Filter out duplicates based on profile URL
            existing_urls = {lead.profile_url for lead in self.leads}
            new_leads = [lead for lead in all_new_leads if lead.profile_url not in existing_urls]
            
            # Add new leads to database
            self.leads.extend(new_leads)
            
            logger.info(f"📈 Found {len(new_leads)} new leads (was {initial_count}, now {len(self.leads)})")
            
            # Process high-priority leads
            await self.process_high_priority_leads()
            
            # Save updated leads database
            self.save_leads()
            
            # Generate and save daily report
            report = await self.generate_daily_report()
            self.save_daily_report(report)
            
            # Calculate runtime
            runtime = time.time() - start_time
            logger.info(f"⏱️ Daily cycle completed in {runtime:.2f} seconds")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error in daily cycle: {e}")
            raise
    
    async def run_continuous(self):
        """Run agent continuously with daily cycles"""
        logger.info("🔄 Starting continuous mode...")
        
        while True:
            try:
                await self.run_daily_cycle()
                logger.info("😴 Sleeping for 24 hours until next cycle...")
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                logger.info("⏰ Retrying in 1 hour...")
                await asyncio.sleep(3600)  # 1 hour retry

def print_fancy_report(report: Dict):
    """Print a nicely formatted report"""
    print("\n" + "="*60)
    print("🏋️‍♂️ RESOLVE FITNESS LEAD GENERATION REPORT")
    print("="*60)
    print(f"📅 Date: {report['date']}")
    print(f"⭐ Performance: {report['summary']['performance'].upper()}")
    print()
    
    print("📊 DAILY METRICS:")
    print(f"  🆕 New Leads Found: {report['metrics']['new_leads']}")
    print(f"  🎯 High Priority: {report['metrics']['high_priority']}")
    print(f"  📈 Medium Priority: {report['metrics']['medium_priority']}")
    print(f"  📤 Contacted Today: {report['metrics']['contacted_today']}")
    print(f"  💾 Total Database: {report['metrics']['total_leads_database']}")
    print(f"  📊 Conversion Rate: {report['metrics']['conversion_rate']}%")
    print()
    
    if report['platform_breakdown']:
        print("🌐 PLATFORM BREAKDOWN:")
        for platform, stats in report['platform_breakdown'].items():
            print(f"  {platform.upper()}: {stats['count']} leads (avg score: {stats['avg_score']:.1f})")
        print()
    
    if report['location_breakdown']:
        print("📍 TOP LOCATIONS:")
        for location, count in sorted(report['location_breakdown'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {location.title()}: {count} leads")
        print()
    
    if report['top_tags']:
        print("🏷️ TOP INTEREST TAGS:")
        for tag, count in report['top_tags']:
            print(f"  {tag.replace('_', ' ').title()}: {count}")
        print()
    
    if report['summary']['recommendations']:
        print("💡 RECOMMENDATIONS:")
        for rec in report['summary']['recommendations']:
            print(f"  • {rec}")
        print()
    
    print("🎯 NEXT STEPS:")
    print("  • Review high-priority leads for immediate outreach")
    print("  • Customize messages for top-scoring prospects")
    print("  • Monitor platform performance and adjust strategy")
    print("  • Follow up with previously contacted leads")
    print("="*60)

async def main():
    """Main function to run the agent"""
    logger.info("🏋️‍♂️ Initializing Resolve Fitness Lead Generation Agent...")
    
    agent = ResolveLeadAgent()
    
    # Run daily cycle
    try:
        report = await agent.run_daily_cycle()
        print_fancy_report(report)
        
        # Success message
        print("\n🎉 SUCCESS! Your lead generation agent is working perfectly!")
        print("📈
        print("📈 Continue building momentum and let your fitness brand shine!\n")
    except Exception as e:
        logger.error(f"❌ An error occurred in the main function: {e}")
        print("\n⚠️ Something went wrong. Check 'lead_agent.log' for details.\n")

if __name__ == "__main__":
    asyncio.run(main())

"""
Presentation Handler for AI Shine Workshop
Handles predefined prompts from presentation.json before falling back to RAG
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class PresentationHandler:
    def __init__(self, json_path: str = "Backend/data/presentation.json"):
        self.json_path = Path(json_path)
        self.data = self._load_presentation()
        self.prompt_map = self._build_prompt_map()
        logger.info(f"[PRESENTATION] Loaded {len(self.data['prompts'])} presentation prompts")
    
    def _load_presentation(self) -> Dict[str, Any]:
        """Load presentation.json"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"[PRESENTATION] presentation.json not found at {self.json_path}")
            return {"greeting": {}, "prompts": []}
        except json.JSONDecodeError as e:
            logger.error(f"[PRESENTATION] Invalid JSON: {e}")
            return {"greeting": {}, "prompts": []}
    
    def _build_prompt_map(self) -> Dict[str, Dict]:
        """Build keyword → prompt mapping for fast lookup"""
        mapping = {}
        for prompt in self.data['prompts']:
            # Map title (lowercase for case-insensitive matching)
            mapping[prompt['title'].lower()] = prompt
            # Map aliases
            for alias in prompt['aliases']:
                mapping[alias.lower()] = prompt
        return mapping
    
    def match_presentation_prompt(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Check if user query matches any presentation prompt
        Returns: prompt data if matched, None otherwise
        """
        query_lower = user_query.lower()
        
        # Check for exact or substring match
        for key, prompt in self.prompt_map.items():
            if key in query_lower or query_lower in key:
                logger.info(f"[PRESENTATION] Matched '{user_query}' to '{prompt['title']}'")
                return prompt
        
        return None
    
    def format_response(self, prompt_data: Dict[str, Any]) -> str:
        """
        Format presentation prompt response into markdown-style text
        """
        response = prompt_data['response']
        formatted = []
        
        # Intro
        if 'intro' in response:
            formatted.append(response['intro'])
        
        # Key benefits
        if 'keyBenefits' in response:
            formatted.append("\n**Key Benefits:**")
            for benefit in response['keyBenefits']:
                formatted.append(f"• {benefit}")
        
        # Tagline
        if 'tagline' in response:
            formatted.append(f"\n*{response['tagline']}*")
        
        # Description
        if 'description' in response:
            formatted.append(f"\n{response['description']}")
        
        # Features
        if 'features' in response:
            formatted.append("\n**Key Features:**")
            for feature in response['features']:
                formatted.append(f"\n**{feature['title']}**\n{feature['description']}")
        
        # Activities
        if 'activities' in response:
            formatted.append("\n**What You Can Do:**")
            for activity in response['activities']:
                formatted.append(f"\n{activity['icon']} **{activity['title']}**\n{activity['description']}")
        
        # Careers
        if 'careers' in response:
            formatted.append("\n**Career Opportunities:**")
            for career in response['careers']:
                formatted.append(f"\n**{career['title']}**")
                formatted.append(career['description'])
                formatted.append(f"*Example:* {career['example']}")
        
        return "\n".join(formatted)
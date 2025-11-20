# rag engine.py
"""
Prompt Builder
Dynamically constructs system prompts with STRICT domain restriction and natural tone.
COMPLETE VERSION - Gemini-safe, no finish_reason=2 errors.
"""
import logging
from typing import Dict, Any, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds dynamic system and user prompts for LLM with strict domain control."""
    
    BASE_SYSTEM_PROMPT = """You are AI Shine, an expert educational assistant specializing in Artificial Intelligence, Machine Learning, and related technologies.

🎯 YOUR IDENTITY:
You are a knowledgeable tutor who explains AI/ML concepts clearly and naturally. You teach as if having a conversation with a curious student—warm, encouraging, and professional.

🔒 STRICT DOMAIN RESTRICTION:
You ONLY teach topics in:
- Artificial Intelligence
- Machine Learning  
- Deep Learning
- Data Science
- Neural Networks
- Natural Language Processing
- Computer Vision
- AI Applications and Ethics
- AI-powered Education
- Programming related to AI/ML (Python, TensorFlow, PyTorch, etc.)

For ANY question outside these domains, you MUST respond with EXACTLY this format (no HTML tags, plain text only):
"⚠️ I specialize in AI and Machine Learning topics. I'd be happy to help with questions about [suggest 2-3 related AI/ML topics]."

NOTE: Start your response with the ⚠️ emoji so the system can detect out-of-scope queries.

⚠️ CRITICAL RULE - NO HALLUCINATION:
You have access to educational content about AI/ML topics. When answering:
1. Use ONLY the knowledge available to you from that content
2. If you don't have specific information, say: "I don't have detailed information about that specific aspect. I can help with [related topics you do know]."
3. NEVER invent examples, statistics, or facts not present in your knowledge
4. NEVER reference "the context," "knowledge base," "provided information," or "sources"
5. Speak as if this is simply what you know as an AI/ML expert
6. If asked about something you truly don't know, acknowledge it naturally and redirect

🗣️ HOW TO COMMUNICATE:
- Explain concepts conversationally (like talking to a student)
- Use examples and analogies when helpful
- Be encouraging and supportive
- Keep tone warm but professional
- NEVER mention internal systems, databases, or retrieval mechanisms
- Speak naturally as if teaching from your expertise
- Vary your wording - don't repeat phrases robotically
- Be human-like in your explanations
- Highlight <strong>key terms</strong>, <strong>tool names</strong>, abbreviations, and important phrases in paragraphs to make explanations more professional and easy to read.

📝 RESPONSE FORMAT - ADAPTIVE HTML STRUCTURE:

<strong>Answer:</strong>

<p>First paragraph with a warm, clear introduction to the topic.</p>

<p>Second paragraph with key explanations or examples from what you know.</p>

<p>Third paragraph (if the topic needs it) with applications or deeper insights.</p>

<strong>Key Points:</strong>
<ul>
<li><strong>Concept/Career 1:</strong> Clear description based on your expertise.</li>
<li><strong>Concept/Career 2:</strong> Practical detail or example.</li>
... (continue for each distinct item)
</ul>

🎨 FORMATTING RULES - MANDATORY:
1. ALWAYS use HTML: <p> for paragraphs, <strong> for bold, <ul><li> for lists
2. Use <strong> for important phrases, points, words, technical terms, abbreviations, tool names, etc. (2-4 words maximum per instance) to emphasize them professionally.
3. Each paragraph MUST be in <p></p> tags
4. For Key Points: 
   - List EVERY distinct, relevant concept, career, or point from the educational content available to you.
   - Do NOT limit to a fixed number—output exactly as many as are present in your knowledge for this query.
   - If the content has 9 careers, list all 9 with their descriptions.
   - If only 3-5 points are justified, stop there. Never add extras or invent items.
   - Format each as: <li><strong>Item Name:</strong> Full description from your expertise. Example if available.</li>
   - Ensure the section title is <strong>Key Points:</strong> and each sub-title (e.g., item name) is bold using <strong>.
5. Bold sparingly—only item names, key terms, or emphasis for professionalism.
6. Paragraphs should be 3-5 sentences each
7. NEVER use markdown (**, *, `) - ONLY HTML
8. NO plain text outside HTML tags
9. Concepts in Key Points should be <strong>

📏 RESPONSE LENGTH:

DEFAULT MODE (Standard Answer):
- 2-3 paragraphs in Answer section
- Key points as many as fit the content
- Total: ~150-250 words
- Focus on clarity and directness

DETAILED MODE (When User Wants More):
Triggered by: "more detail", "elaborate", "tell me more", "explain further", "go deeper", "continue"
- 4-6 paragraphs in Answer section
- Detailed key points as many as fit the content (expand descriptions)
- Include practical examples and applications
- Add use cases or tips when relevant
- Total: ~300-450 words
- Be comprehensive but stay focused

⚠️ WHEN INFORMATION IS LIMITED:
If you lack details to answer fully:
"I don't have comprehensive information about [specific aspect]. I can explain [related concepts you do know about]."

Don't apologize excessively. Be direct and helpful.

🚫 WHAT YOU MUST NEVER DO:
- Mention "context," "knowledge base," "documents," or "retrieved information"
- Say "according to" or "based on the provided content"
- Reference data structures, databases, or internal systems
- Use phrases like "the source states" or "from the documentation"
- Break the fourth wall about how you access information
- Acknowledge retrieval mechanisms or RAG systems
- Invent facts, examples, or statistics not in your knowledge
- Use exact same phrasing repeatedly (vary your language naturally)

✅ REMEMBER:
You're an AI/ML expert teaching a student. The knowledge you share comes naturally from your expertise. Be helpful, accurate, and never make things up. If you don't know something specific, redirect to what you do know. Speak naturally and vary your explanations.

Finish your complete response. Never stop in the middle of a sentence or bullet point."""
    
    # Continuation patterns
    CONTINUATION_PATTERNS = [
        r'\btell\s+me\s+more\b',
        r'\belaborate\b',
        r'\bgo\s+deeper\b',
        r'\bexpand\b',
        r'\bmore\s+detail',
        r'\bcontinue\b',
        r'\bkeep\s+going\b',
        r'\bwhat\s+else\b',
        r'\bexplain\s+further\b',
        r'\bgo\s+on\b',
        r'^\s*and\s*\??\s*$',
        r'^\s*more\s*\??\s*$',
        r'^\s*continue\s*\??\s*$',
        r'\btell\s+me\s+about',
        r'\bgive\s+me\s+more',
        r'\bcan\s+you\s+elaborate'
    ]
    
    # Greeting detection
    GREETING_PATTERNS = [
        r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\s*[!.,]?\s*$'
    ]
    
    # Farewell detection
    FAREWELL_PATTERNS = [
        r'^\s*(bye|goodbye|see\s+you|farewell|ttyl|later|ciao|adios)\s*[!.,]?\s*$'
    ]
    
    # Presentation prompt patterns (deterministic exact match)
    PRESENTATION_PROMPTS = {
        "ai in maths mastery": "AI in Maths Mastery",
        "maths mastery": "AI in Maths Mastery",
        "math mastery": "AI in Maths Mastery",
        "future careers powered by ai": "Future Careers Powered by AI",
        "future careers": "Future Careers Powered by AI",
        "ai careers": "Future Careers Powered by AI",
        "careers in ai": "Future Careers Powered by AI",
        "why ai for students": "Why AI for Students",
        "why ai": "Why AI for Students",
        "ai for students": "Why AI for Students",
        "ai in science labs": "AI in Science Labs",
        "science labs": "AI in Science Labs",
        "ai science": "AI in Science Labs"
    }

    def __init__(self):
        self.continuation_regex = re.compile('|'.join(self.CONTINUATION_PATTERNS), re.IGNORECASE)
        self.greeting_regex = re.compile('|'.join(self.GREETING_PATTERNS), re.IGNORECASE)
        self.farewell_regex = re.compile('|'.join(self.FAREWELL_PATTERNS), re.IGNORECASE)
    
    def detect_intent(self, message: str, chat_history: list = None) -> Dict[str, Any]:
        """
        Detect intent from user message.
        
        Args:
            message: Current user message
            chat_history: Previous messages (for context, unused in regex detection)
        
        Returns:
            Dict with 'intent_type', 'is_continuation', 'is_greeting', 'is_farewell', 'is_presentation', 'presentation_topic', 'confidence'
        """
        if not message or not message.strip():
            logger.warning("[INTENT] Empty message")
            return {
                "intent_type": "query",
                "is_continuation": False,
                "is_greeting": False,
                "is_farewell": False,
                "is_presentation": False,
                "presentation_topic": None,
                "confidence": 0.0
            }
        
        message = message.strip()
        message_lower = message.lower()
        
        # 1. Check for greeting (fast regex)
        is_greeting = bool(self.greeting_regex.match(message))
        if is_greeting:
            logger.info("[INTENT] Greeting detected (regex)")
            return {
                "intent_type": "greeting",
                "is_continuation": False,
                "is_greeting": True,
                "is_farewell": False,
                "is_presentation": False,
                "presentation_topic": None,
                "confidence": 1.0
            }
        
        # 2. Check for farewell (fast regex)
        is_farewell = bool(self.farewell_regex.match(message))
        if is_farewell:
            logger.info("[INTENT] Farewell detected (regex)")
            return {
                "intent_type": "farewell",
                "is_continuation": False,
                "is_greeting": False,
                "is_farewell": True,
                "is_presentation": False,
                "presentation_topic": None,
                "confidence": 1.0
            }
        
        # 3. Check for presentation prompt (deterministic)
        for key, topic in self.PRESENTATION_PROMPTS.items():
            if key in message_lower:
                logger.info(f"[INTENT] Presentation prompt detected: {topic}")
                return {
                    "intent_type": "presentation",
                    "is_continuation": False,
                    "is_greeting": False,
                    "is_farewell": False,
                    "is_presentation": True,
                    "presentation_topic": topic,
                    "confidence": 1.0
                }
        
        # 4. Check for continuation cues (fast regex)
        is_continuation = bool(self.continuation_regex.search(message))
        if is_continuation:
            logger.info("[INTENT] Continuation detected (regex)")
            return {
                "intent_type": "continuation",
                "is_continuation": True,
                "is_greeting": False,
                "is_farewell": False,
                "is_presentation": False,
                "presentation_topic": None,
                "confidence": 1.0
            }
        
        # 5. Default: standard query
        logger.info("[INTENT] Standard query")
        return {
            "intent_type": "query",
            "is_continuation": False,
            "is_greeting": False,
            "is_farewell": False,
            "is_presentation": False,
            "presentation_topic": None,
            "confidence": 1.0
        }
    
    def build_system_prompt(
        self,
        intent: Dict[str, Any],
        has_context: bool = True,
        is_presentation: bool = False
    ) -> str:
        """
        Build system prompt based on intent, context availability, and source type.
        
        Args:
            intent: Intent dict from detect_intent
            has_context: Whether RAG retrieved relevant context
            is_presentation: Whether context is from presentation.json
        
        Returns:
            System prompt string
        """
        system_prompt = self.BASE_SYSTEM_PROMPT
        
        # Internal note for presentation content (not shown to user)
        if is_presentation:
            system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
            system_prompt += "\n🎓 PRESENTATION MODE:"
            system_prompt += "\nThe content available is introductory workshop material."
            system_prompt += "\n- Keep tone especially friendly and encouraging"
            system_prompt += "\n- Focus on practical applications for students"
            system_prompt += "\n- Use accessible, simple language"
            system_prompt += "\n- Emphasize benefits and real-world relevance"
            system_prompt += "\n- If asked for advanced details beyond scope, naturally acknowledge:"
            system_prompt += "\n  'That gets into more advanced territory. Let me explain the core concept first...'"
            system_prompt += "\n- NEVER say 'presentation' or 'introductory content' directly to the user\n"
            system_prompt += "\n- The number of Key Points should ideally be from 9-10\n"
        
        # Detailed mode for continuations
        if intent.get('is_continuation', False):
            system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
            system_prompt += "\n🔥 DETAILED MODE ACTIVATED:"
            system_prompt += "\nThe user wants MORE detailed information."
            system_prompt += "\nProvide a thorough explanation:"
            system_prompt += "\n- Write 4-6 paragraphs in <p> tags with proper HTML formatting"
            system_prompt += "\n- Include concrete examples, analogies, and real-world applications"
            system_prompt += "\n- Add practical tips, tools, or use cases"
            system_prompt += "\n- Provide detailed key points in <ul><li> format—as many as fit the content"
            system_prompt += "\n- Use <strong> for technical terms only (2-4 words max)"
            system_prompt += "\n- Be comprehensive, engaging, and educational"
            system_prompt += "\n- Teach deeply using ONLY the knowledge available to you\n"
        
        # No context available
        if not has_context:
            system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
            system_prompt += "\n⚠️ NO INFORMATION AVAILABLE:"
            system_prompt += "\nYou don't have knowledge to answer this specific query."
            system_prompt += "\nRespond naturally:"
            system_prompt += "\n'I don't have specific information about that. I can help with topics like [list 2-3 related AI/ML topics].'"
            system_prompt += "\nBe brief and redirect to your areas of expertise. Don't over-apologize.\n"
        
        logger.info(f"[PROMPT_BUILD] Intent: {intent.get('intent_type')}, Has context: {has_context}, Presentation: {is_presentation}, Continuation: {intent.get('is_continuation', False)}")
        return system_prompt
    
    def build_user_prompt(
        self,
        query: str,
        context_chunks: List[str],
        intent: Dict[str, Any],
        is_presentation: bool = False
    ) -> str:
        """
        Build user prompt with query and retrieved context.
        Context is injected invisibly—LLM internalizes it as background knowledge.
        
        Args:
            query: User's question
            context_chunks: Retrieved context from RAG
            intent: Intent dict
            is_presentation: Whether context is from presentation
        
        Returns:
            Formatted user prompt
        """
        if not context_chunks:
            # No context available
            user_prompt = f"""[No educational content available for this query]

User Question: {query}

⚠️ You don't have information to answer this. Respond naturally that you don't have details about this specific topic, and suggest related AI/ML topics you can help with."""
            return user_prompt
        
        # Build hidden context section (LLM internalizes this as knowledge)
        context_section = "[Educational content for reference - internalize as your expertise]:\n\n"
        
        # Truncate each chunk to save tokens while preserving meaning
        for idx, chunk in enumerate(context_chunks[:3], 1):  # Max 3 chunks
            truncated_chunk = chunk[:800] + "..." if len(chunk) > 800 else chunk
            context_section += f"{truncated_chunk}\n\n"
        
        context_section += "---\n\n"
        
        # Build final prompt
        user_prompt = context_section
        user_prompt += f"Student Question: {query}\n\n"
        
        # Detect if this is a list-heavy query (e.g., careers)
        is_list_query = any(keyword in query.lower() for keyword in ['careers', 'roles', 'jobs', 'list of']) or 'careers' in ''.join(context_chunks).lower()
        
        if is_presentation or is_list_query:
            user_prompt += """Present the content above naturally, focusing on lists if present.

Format:
<strong>Answer:</strong>
<p>2-3 paragraphs introducing the topic.</p>

<strong>Key Points:</strong>
<ul>
<li><strong>Item Name:</strong> Full description from content. Example: example text.</li>
... (repeat for EVERY item)
</ul>

Rules:
1. If the content includes a list (e.g., careers), include EVERY single item as a separate <li>.
2. Use exact titles, descriptions, and examples from the content—do not skip, merge, or add.
3. Count the items in the content and output that exact number of <li> tags.
4. For non-list topics, use 3-5 points as natural.
5. Complete the full list before ending.
6. HTML formatting only
7. Never mention sources"""
            return user_prompt
        
        # Instructions based on mode (continuation vs standard)
        if intent.get('is_continuation', False):
            user_prompt += """Provide detailed explanation:
- Write 4-6 paragraphs in <p> tags
- Include key points in <ul><li> with <strong> on terms—as many as fit the content.
- Add examples and use cases
- HTML formatting only
- Never mention sources"""
        else:
            user_prompt += """Provide clear answer:
- Write 2-3 paragraphs in <p> tags
- Include key points in <ul><li> with <strong> on terms—as many as naturally fit (e.g., all from content for lists).
- HTML formatting only
- Never mention sources"""
        
        return user_prompt

    def build_greeting_response(self) -> str:
        """Build a welcoming greeting response."""
        return "👋 Hello! I'm <strong>AI Shine</strong>, your AI/ML educational assistant. Ask me anything about Artificial Intelligence, Machine Learning, or AI-powered education!"

    def build_farewell_response(self) -> str:
        """Build a warm farewell response for when the user says bye."""
        return "👋 Goodbye! It was great chatting with you about AI and ML. Feel free to come back anytime for more learning!"


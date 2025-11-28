"""
Prompt Builder
KB-locked, complete enumerations, deterministic continuation with <<CONTINUE>>,
proper formatting with blank lines between paragraphs and list items.
Backward-compatible signatures.
"""

import logging
import re
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    - Strict domain: AI/ML, DL, DS, NLP, CV, AI apps/ethics, AI programming.
    - Knowledge-lock: Use ONLY injected KB content; append minimal general AI ONLY if KB is insufficient.
    - HTML-only: <p>, <ul><li>, <strong>; one blank line between <p> blocks AND between <li> items.
    - Complete lists in all modes; never omit items (titles at minimum).
    - Brief mode: items 1–3 full, items 4..N titles only (no collapsing, no Learn more).
    - Detailed/Continue mode: extend without restarting; finish remaining KB items first.
    - CONTINUE marker: if token-limited, end with <<CONTINUE>> on its own line so the client resumes.
    - No keywords display, no Key Points section.
    - Backward-compatible API: accepts is_presentation param but ignores it.
    """

    BASE_SYSTEM_PROMPT = """You are AI Shine, an expert educational assistant specializing in Artificial Intelligence, Machine Learning, and related technologies.

Identity:
- Teach clearly and naturally with a warm, encouraging, professional tone. Keep small talk minimal.

Scope (strict):
- Only answer topics in: Artificial Intelligence, Machine Learning, Deep Learning, Data Science, Natural Language Processing, Computer Vision, AI Applications and Ethics, AI-powered Education, Programming for AI/ML (e.g., Python, TensorFlow, PyTorch).
- If out-of-scope, respond exactly (plain text, no HTML):
"⚠️ I specialize in AI and Machine Learning topics. I'd be happy to help with questions about [suggest 2-3 related AI/ML topics]."
- Start that out-of-scope line with the ⚠️ emoji.

Knowledge-lock (critical):
- Use ONLY the provided educational content for this turn. Do NOT add roles, items, examples, claims, steps, or statistics that are not present in the content.
- HALLUCINATION GUARDRAIL: If the KB content mentions a concept (e.g., "machine learning") but doesn't provide a complete definition, structure your answer as follows:
  [1] Lead with a clear, concise definition using your AI/ML training knowledge
  [2] Then naturally integrate KB examples and applications (e.g., "It's used in Netflix recommendations for...")
  [3] Do NOT start with phrases like "The provided content doesn't define..." or "From a general AI perspective..." - just provide the definition directly and weave in KB examples
- If the KB has NO information on a domain-specific AI/ML topic, you may provide a brief, accurate definition from your training knowledge, but acknowledge that specific applications aren't in the provided materials.
- NEVER invent examples, statistics, specific claims, roles, or applications that are not present in the KB content. Only provide general definitions when absolutely necessary.
- If details are missing, structure as: "[Clear definition]. Based on the content, [integrate KB examples]."
- Do NOT switch to prompting frameworks unless explicitly asked.

Output format (HTML only):
- Use <p> for paragraphs and insert a single blank line between consecutive <p> blocks.
- Use <strong> for key terms (2–4 words). Use <ul><li> for key points.
- Insert a single blank line between each <li> item in lists for better readability.
- CRITICAL: ALL content must be wrapped in proper HTML tags. Never output plain text lines without tags.
- For any bulleted or numbered content, ALWAYS use <ul><li> or <ol><li> tags.
- Never use plain text bullets (•, -, *) without wrapping in <li> tags.
- Never output raw text paragraphs - always wrap in <p> tags.
- No markdown; no plain text outside HTML (except the out-of-scope line).

EXAMPLE OF CORRECT FORMATTING:
<p>AI significantly aids in visualizing complex topics by transforming abstract information into intelligent, digestible visuals.</p>

<p>Here are some ways AI helps:</p>

<ul>
<li>AI can create labeled diagrams for scientific concepts (e.g., human heart, digestive system)</li>

<li>It can animate processes like mitosis or the water cycle</li>

<li>AI excels at converting tables into colorful charts (pie, bar, line)</li>
</ul>

INCORRECT (NEVER DO THIS):
AI can create labeled diagrams for scientific concepts
It can animate processes like mitosis
AI excels at converting tables into charts

Enumeration policy (complete in all modes):
- If the KB content has a numbered/bulleted list, ensure EVERY item appears.
- In brief mode for generic lists:
  - Show the first 3 items with full descriptions.
  - Show items 4..N as titles in the main <ul>.
  - Do NOT use collapsing or Learn more buttons - show all items inline with their full descriptions.
- In the special topic "Future Careers Powered by AI":
  - Show items 1–8 with full descriptions in the main <ul>.
  - Show item 9 with full description as well - no collapsing.
- Do NOT add, merge, rename, or omit items. Use ONLY KB-provided examples/details.

Detailed/Continue behavior:
- For "continue", "more detail", "elaborate", "go deeper", etc.:
  - Do NOT restate earlier content; extend using ONLY details present in the KB.
  - If a list began earlier, resume at the next item and complete all remaining KB items before adding extra depth.
  - Aim for 4–6 <p> paragraphs.

Chunking and continuation marker (for long outputs):
- Write in logically complete sections. If you must stop before completing all sections or list items,
  end the message with this exact token on its own line: <<CONTINUE>>
- On the next turn, resume exactly where you stopped without repeating earlier content.

KB-first with minimal append:
- Only after fully using the KB content may you append minimal, generic AI knowledge to fill gaps; keep such additions short and aligned with the KB.
- Never add or replace list items beyond those in the KB.
"""

    # Continuation cues
    CONTINUATION_PATTERNS = [
        r'\btell\s+me\s+more\b', r'\belaborate\b', r'\bgo\s+deeper\b', r'\bexpand\b',
        r'\bmore\s+detail\b', r'\bexplain\s+further\b', r'\bkeep\s+going\b', r'\bwhat\s+else\b',
        r'\bcontinue\b', r'\bgo\s+on\b', r'^\s*and\s*\??\s*$', r'^\s*more\s*\??\s*$',
        r'^\s*continue\s*\??\s*$',
    ]

    GREETING_PATTERNS = [r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\s*[!.,]?\s*$']
    FAREWELL_PATTERNS = [r'^\s*(bye|goodbye|see\s+you|farewell|ttyl|later|ciao|adios)\s*[!.,]?\s*$']

    # Larger packing to preserve full lists
    MAX_CONTEXT_CHUNKS = 3
    CHUNK_TRUNCATE_CHARS = 3000

    def __init__(self):
        self.continuation_regex = re.compile('|'.join(self.CONTINUATION_PATTERNS), re.IGNORECASE)
        self.greeting_regex = re.compile('|'.join(self.GREETING_PATTERNS), re.IGNORECASE)
        self.farewell_regex = re.compile('|'.join(self.FAREWELL_PATTERNS), re.IGNORECASE)

    def detect_intent(self, message: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not message or not message.strip():
            return {"intent_type": "query", "is_continuation": False, "is_greeting": False, "is_farewell": False, "confidence": 0.0}
        text = message.strip()
        if self.greeting_regex.match(text):
            return {"intent_type": "greeting", "is_continuation": False, "is_greeting": True, "is_farewell": False, "confidence": 1.0}
        if self.farewell_regex.match(text):
            return {"intent_type": "farewell", "is_continuation": False, "is_greeting": False, "is_farewell": True, "confidence": 1.0}
        if self.continuation_regex.search(text):
            return {"intent_type": "continuation", "is_continuation": True, "is_greeting": False, "is_farewell": False, "confidence": 1.0}
        return {"intent_type": "query", "is_continuation": False, "is_greeting": False, "is_farewell": False, "confidence": 1.0}

    def build_system_prompt(
        self,
        intent: Dict[str, Any],
        has_context: bool = True,
        is_presentation: bool = False  # ignored, kept for compatibility
    ) -> str:
        system_prompt = self.BASE_SYSTEM_PROMPT

        if intent.get("is_continuation", False):
            system_prompt += (
                "\n\n[INTERNAL NOTE - Not visible to user]\n"
                "Detailed/Continue Mode:\n"
                "- Extend prior answer without repeating.\n"
                "- Resume and complete any KB-derived lists before adding extra depth.\n"
                "- Use only KB details; append minimal general AI info only if KB is insufficient.\n"
                "- 4–6 <p> paragraphs.\n"
            )
        if not has_context:
            system_prompt += (
                "\n\n[INTERNAL NOTE - Not visible to user]\n"
                "No KB content available. Be brief: acknowledge limited details and offer related AI/ML topics.\n"
            )

        return system_prompt

    def _pack_context(self, context_chunks: List[str]) -> str:
        if not context_chunks:
            return ""
        section = "[Educational content (treat as your expertise for THIS TURN ONLY)]:\n\n"
        added = 0
        for chunk in context_chunks:
            if not chunk:
                continue
            truncated = chunk[: self.CHUNK_TRUNCATE_CHARS]
            if len(chunk) > self.CHUNK_TRUNCATE_CHARS:
                truncated += "..."
            section += truncated + "\n\n"
            added += 1
            if added >= self.MAX_CONTEXT_CHUNKS:
                break
        section += "---\n\n"
        return section

    def build_user_prompt(
        self,
        query: str,
        context_chunks: List[str],
        intent: Dict[str, Any],
        is_presentation: bool = False,  # ignored
        show_module_citation: bool = False,
        module_names: Optional[List[str]] = None,
        use_learn_more: bool = True
    ) -> str:
        if not context_chunks:
            return (
                "[No educational content available for this query]\n\n"
                f"User Question: {query}\n\n"
                "You don't have detailed information for this specific aspect. "
                "Respond briefly and suggest related AI/ML topics you can help with."
            )

        user_prompt = self._pack_context(context_chunks)
        user_prompt += f"Student Question: {query}\n\n"

        ql = (query or "").lower()
        hardlock_careers = (
            "future careers powered by ai" in ql
            or "careers in ai" in ql
            or "ai careers" in ql
        )

        # Optional footer citation
        footer_note = ""
        if show_module_citation and module_names:
            unique = [m for m in dict.fromkeys(module_names) if m]
            if unique:
                footer_note = f'\n- At the very end, append: <p><em>Source: {", ".join(unique)}</em></p>'

        # continue_rule = "\n- If you must stop before completing all sections or list items, end with a line containing exactly: <<CONTINUE>>"
        continue_rule = "\n- If you must stop before completing all sections or list items, end with: <p><em>Write 'continue' to keep generating...</em></p>"

        if intent.get("is_continuation", False):
            user_prompt += (
                "FORMATTING REQUIREMENT: Your entire response must use proper HTML tags.\n"
                "- Every paragraph must be wrapped in <p>...</p>\n"
                "- Every list item must be wrapped in <li>...</li> inside <ul>...</ul>\n"
                "- Never output plain text without HTML tags.\n\n"
                "HALLUCINATION GUARDRAIL: Use ONLY details from the KB content above. If you need to add general AI/ML knowledge to complete the explanation, clearly indicate what comes from the KB vs. your general knowledge. NEVER invent specific examples, statistics, or applications not in the KB.\n\n"
                "Provide a deeper continuation using the content above (do not restate previous content):\n"
                "- Write 4–6 paragraphs in <p> tags with NEW KB-backed details. Insert one blank line between paragraphs.\n"
                "- If a list began earlier, continue at the next item and complete all remaining KB items before adding extra depth.\n"
                "- CRITICAL: Wrap ALL list items in <ul><li> tags with a blank line between each <li>.\n"
                "- CRITICAL: Wrap ALL paragraphs in <p> tags. Never output plain text without HTML tags.\n"
                "- Use <strong> sparingly (2–4 words). HTML only; do not mention sources."
                f"{continue_rule}"
                f"{footer_note}"
            )
            return user_prompt

        if hardlock_careers:
            # Special rendering: items 1–8 full; item 9 with full description as well
            user_prompt += (
                "FORMATTING REQUIREMENT: Your entire response must use proper HTML tags.\n"
                "- Every paragraph must be wrapped in <p>...</p>\n"
                "- Every list item must be wrapped in <li>...</li> inside <ul>...</ul>\n"
                "- Never output plain text without HTML tags.\n\n"
                "HALLUCINATION GUARDRAIL: Render careers STRICTLY from the KB above. Do NOT add careers, examples, or descriptions not present in the KB. If you need to add brief general context about AI careers, keep it minimal and clearly separate from the KB-sourced list.\n\n"
                "Render the careers STRICTLY from the KB above:\n"
                "- Write 2–3 paragraphs in <p> tags (insert a blank line between paragraphs).\n"
                "- Then output a <ul> that lists ALL 9 items exactly as titled in the KB.\n"
                "- Provide full descriptions for ALL 9 items in the main <ul>.\n"
                "- Insert a single blank line between each <li> item for readability.\n"
                "- CRITICAL: ALL list items must be wrapped in <li> tags. Never use plain text bullets.\n"
                "- Do NOT add generic filler or extra careers. HTML only."
                f"{continue_rule}"
                f"{footer_note}"
            )
            return user_prompt

        # Generic brief-but-complete list rendering for all other topics
        user_prompt += (
            "FORMATTING REQUIREMENT: Your entire response must use proper HTML tags.\n"
            "- Every paragraph must be wrapped in <p>...</p>\n"
            "- Every list item must be wrapped in <li>...</li> inside <ul>...</ul>\n"
            "- Never output plain text without HTML tags.\n\n"
            "HALLUCINATION GUARDRAIL: Synthesize your answer from the KB content above. If the KB mentions a concept but doesn't fully define it (e.g., mentions 'machine learning' in examples):\n"
            "[1] Lead with a clear definition using your AI/ML training knowledge\n"
            "[2] Then naturally integrate KB examples (e.g., 'It's used in Netflix recommendations for...')\n"
            "[3] Do NOT start with 'The provided content doesn't define...' - just provide the definition and weave in KB examples\n"
            "NEVER invent specific examples, tools, statistics, or applications not in the KB. Only provide general conceptual definitions when needed.\n\n"
            "Provide a concise, KB-first answer:\n"
            "- Write 2–3 paragraphs in <p> tags; insert a blank line between them.\n"
            "- If the KB contains a numbered/bulleted list, output EVERY item with full description:\n"
            "  • Show items 1–3 with full descriptions in the main <ul>.\n"
            "  • Show items 4..N with full descriptions in the main <ul> as well.\n"
            "  • Insert a single blank line between each <li> item for readability.\n"
            "  • CRITICAL: ALL list items must be wrapped in <li> tags. Never use plain text bullets.\n"
            "- CRITICAL: ALL paragraphs must be wrapped in <p> tags. Never output plain text without HTML tags.\n"
            "- Do NOT add or omit items; use only KB-provided examples.\n"
            "- Use <strong> for key terms (2–4 words)."
            f"{continue_rule}"
            f"{footer_note}"
        )
        return user_prompt

    def build_greeting_response(self) -> str:
        return (
            "👋 Hello! I'm <strong>AI Shine</strong>, your AI/ML educational assistant. "
            "Ask anything about <strong>AI</strong>, <strong>Machine Learning</strong>, "
            "<strong>Data Science</strong>, <strong>NLP</strong>, or <strong>Computer Vision</strong>!"
        )

    def build_farewell_response(self) -> str:
        return (
            "👋 Goodbye! It was great chatting about <strong>AI</strong> and <strong>ML</strong>. "
            "Come back anytime to learn more!"
        )












# """
# Prompt Builder
# Dynamically constructs system prompts with STRICT domain restriction and natural tone.
# COMPLETE VERSION - Gemini-safe, no finish_reason=2 errors.
# """
# import logging
# from typing import Dict, Any, List
# import re

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class PromptBuilder:
#     """Builds dynamic system and user prompts for LLM with strict domain control."""
    
#     BASE_SYSTEM_PROMPT = """You are AI Shine, an expert educational assistant specializing in Artificial Intelligence, Machine Learning, and related technologies.

# 🎯 YOUR IDENTITY:
# You are a knowledgeable tutor who explains AI/ML concepts clearly and naturally. You teach as if having a conversation with a curious student—warm, encouraging, and professional.

# 🔒 STRICT DOMAIN RESTRICTION:
# You ONLY teach topics in:
# - Artificial Intelligence
# - Machine Learning  
# - Deep Learning
# - Data Science
# - Neural Networks
# - Natural Language Processing
# - Computer Vision
# - AI Applications and Ethics
# - AI-powered Education
# - Programming related to AI/ML (Python, TensorFlow, PyTorch, etc.)

# For ANY question outside these domains, you MUST respond with EXACTLY this format (no HTML tags, plain text only):
# "⚠️ I specialize in AI and Machine Learning topics. I'd be happy to help with questions about [suggest 2-3 related AI/ML topics]."

# NOTE: Start your response with the ⚠️ emoji so the system can detect out-of-scope queries.

# ⚠️ CRITICAL RULE - NO HALLUCINATION:
# You have access to educational content about AI/ML topics. When answering:
# 1. Use ONLY the knowledge available to you from that content
# 2. If you don't have specific information, say: "I don't have detailed information about that specific aspect. I can help with [related topics you do know]."
# 3. NEVER invent examples, statistics, or facts not present in your knowledge
# 4. NEVER reference "the context," "knowledge base," "provided information," or "sources"
# 5. Speak as if this is simply what you know as an AI/ML expert
# 6. If asked about something you truly don't know, acknowledge it naturally and redirect

# 🗣️ HOW TO COMMUNICATE:
# - Explain concepts conversationally (like talking to a student)
# - Use examples and analogies when helpful
# - Be encouraging and supportive
# - Keep tone warm but professional
# - NEVER mention internal systems, databases, or retrieval mechanisms
# - Speak naturally as if teaching from your expertise
# - Vary your wording - don't repeat phrases robotically
# - Be human-like in your explanations
# - Highlight <strong>key terms</strong>, <strong>tool names</strong>, abbreviations, and important phrases in paragraphs to make explanations more professional and easy to read.

# 📝 RESPONSE FORMAT - ADAPTIVE HTML STRUCTURE:

# <strong>Answer:</strong>

# <p>First paragraph with a warm, clear introduction to the topic.</p>

# <p>Second paragraph with key explanations or examples from what you know.</p>

# <p>Third paragraph (if the topic needs it) with applications or deeper insights.</p>

# <strong>Key Points:</strong>
# <ul>
# <li><strong>Concept/Career 1:</strong> Clear description based on your expertise.</li>
# <li><strong>Concept/Career 2:</strong> Practical detail or example.</li>
# ... (continue for each distinct item)
# </ul>

# 🎨 FORMATTING RULES - MANDATORY:
# 1. ALWAYS use HTML: <p> for paragraphs, <strong> for bold, <ul><li> for lists
# 2. Use <strong> for important phrases, points, words, technical terms, abbreviations, tool names, etc. (2-4 words maximum per instance) to emphasize them professionally.
# 3. Each paragraph MUST be in <p></p> tags
# 4. For Key Points: 
#    - List EVERY distinct, relevant concept, career, or point from the educational content available to you.
#    - Do NOT limit to a fixed number—output exactly as many as are present in your knowledge for this query.
#    - If the content has 9 careers, list all 9 with their descriptions.
#    - If only 3-5 points are justified, stop there. Never add extras or invent items.
#    - Format each as: <li><strong>Item Name:</strong> Full description from your expertise. Example if available.</li>
#    - Ensure the section title is <strong>Key Points:</strong> and each sub-title (e.g., item name) is bold using <strong>.
# 5. Bold sparingly—only item names, key terms, or emphasis for professionalism.
# 6. Paragraphs should be 3-5 sentences each
# 7. NEVER use markdown (**, *, `) - ONLY HTML
# 8. NO plain text outside HTML tags
# 9. Concepts in Key Points should be <strong>

# 📏 RESPONSE LENGTH:

# DEFAULT MODE (Standard Answer):
# - 2-3 paragraphs in Answer section
# - Key points as many as fit the content
# - Total: ~150-250 words
# - Focus on clarity and directness

# DETAILED MODE (When User Wants More):
# Triggered by: "more detail", "elaborate", "tell me more", "explain further", "go deeper", "continue"
# - 4-6 paragraphs in Answer section
# - Detailed key points as many as fit the content (expand descriptions)
# - Include practical examples and applications
# - Add use cases or tips when relevant
# - Total: ~300-450 words
# - Be comprehensive but stay focused

# ⚠️ WHEN INFORMATION IS LIMITED:
# If you lack details to answer fully:
# "I don't have comprehensive information about [specific aspect]. I can explain [related concepts you do know about]."

# Don't apologize excessively. Be direct and helpful.

# 🚫 WHAT YOU MUST NEVER DO:
# - Mention "context," "knowledge base," "documents," or "retrieved information"
# - Say "according to" or "based on the provided content"
# - Reference data structures, databases, or internal systems
# - Use phrases like "the source states" or "from the documentation"
# - Break the fourth wall about how you access information
# - Acknowledge retrieval mechanisms or RAG systems
# - Invent facts, examples, or statistics not in your knowledge
# - Use exact same phrasing repeatedly (vary your language naturally)

# ✅ REMEMBER:
# You're an AI/ML expert teaching a student. The knowledge you share comes naturally from your expertise. Be helpful, accurate, and never make things up. If you don't know something specific, redirect to what you do know. Speak naturally and vary your explanations.

# Finish your complete response. Never stop in the middle of a sentence or bullet point."""
    
#     # Continuation patterns
#     CONTINUATION_PATTERNS = [
#         r'\btell\s+me\s+more\b',
#         r'\belaborate\b',
#         r'\bgo\s+deeper\b',
#         r'\bexpand\b',
#         r'\bmore\s+detail',
#         r'\bcontinue\b',
#         r'\bkeep\s+going\b',
#         r'\bwhat\s+else\b',
#         r'\bexplain\s+further\b',
#         r'\bgo\s+on\b',
#         r'^\s*and\s*\??\s*$',
#         r'^\s*more\s*\??\s*$',
#         r'^\s*continue\s*\??\s*$',
#         r'\btell\s+me\s+about',
#         r'\bgive\s+me\s+more',
#         r'\bcan\s+you\s+elaborate'
#     ]
    
#     # Greeting detection
#     GREETING_PATTERNS = [
#         r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\s*[!.,]?\s*$'
#     ]
    
#     # Farewell detection
#     FAREWELL_PATTERNS = [
#         r'^\s*(bye|goodbye|see\s+you|farewell|ttyl|later|ciao|adios)\s*[!.,]?\s*$'
#     ]
    
#     # Presentation prompt patterns (deterministic exact match)
#     PRESENTATION_PROMPTS = {
#         "ai in maths mastery": "AI in Maths Mastery",
#         "maths mastery": "AI in Maths Mastery",
#         "math mastery": "AI in Maths Mastery",
#         "future careers powered by ai": "Future Careers Powered by AI",
#         "future careers": "Future Careers Powered by AI",
#         "ai careers": "Future Careers Powered by AI",
#         "careers in ai": "Future Careers Powered by AI",
#         "why ai for students": "Why AI for Students",
#         "why ai": "Why AI for Students",
#         "ai for students": "Why AI for Students",
#         "ai in science labs": "AI in Science Labs",
#         "science labs": "AI in Science Labs",
#         "ai science": "AI in Science Labs"
#     }

#     def __init__(self):
#         self.continuation_regex = re.compile('|'.join(self.CONTINUATION_PATTERNS), re.IGNORECASE)
#         self.greeting_regex = re.compile('|'.join(self.GREETING_PATTERNS), re.IGNORECASE)
#         self.farewell_regex = re.compile('|'.join(self.FAREWELL_PATTERNS), re.IGNORECASE)
    
#     def detect_intent(self, message: str, chat_history: list = None) -> Dict[str, Any]:
#         """
#         Detect intent from user message.
        
#         Args:
#             message: Current user message
#             chat_history: Previous messages (for context, unused in regex detection)
        
#         Returns:
#             Dict with 'intent_type', 'is_continuation', 'is_greeting', 'is_farewell', 'is_presentation', 'presentation_topic', 'confidence'
#         """
#         if not message or not message.strip():
#             logger.warning("[INTENT] Empty message")
#             return {
#                 "intent_type": "query",
#                 "is_continuation": False,
#                 "is_greeting": False,
#                 "is_farewell": False,
#                 "is_presentation": False,
#                 "presentation_topic": None,
#                 "confidence": 0.0
#             }
        
#         message = message.strip()
#         message_lower = message.lower()
        
#         # 1. Check for greeting (fast regex)
#         is_greeting = bool(self.greeting_regex.match(message))
#         if is_greeting:
#             logger.info("[INTENT] Greeting detected (regex)")
#             return {
#                 "intent_type": "greeting",
#                 "is_continuation": False,
#                 "is_greeting": True,
#                 "is_farewell": False,
#                 "is_presentation": False,
#                 "presentation_topic": None,
#                 "confidence": 1.0
#             }
        
#         # 2. Check for farewell (fast regex)
#         is_farewell = bool(self.farewell_regex.match(message))
#         if is_farewell:
#             logger.info("[INTENT] Farewell detected (regex)")
#             return {
#                 "intent_type": "farewell",
#                 "is_continuation": False,
#                 "is_greeting": False,
#                 "is_farewell": True,
#                 "is_presentation": False,
#                 "presentation_topic": None,
#                 "confidence": 1.0
#             }
        
#         # 3. Check for presentation prompt (deterministic)
#         for key, topic in self.PRESENTATION_PROMPTS.items():
#             if key in message_lower:
#                 logger.info(f"[INTENT] Presentation prompt detected: {topic}")
#                 return {
#                     "intent_type": "presentation",
#                     "is_continuation": False,
#                     "is_greeting": False,
#                     "is_farewell": False,
#                     "is_presentation": True,
#                     "presentation_topic": topic,
#                     "confidence": 1.0
#                 }
        
#         # 4. Check for continuation cues (fast regex)
#         is_continuation = bool(self.continuation_regex.search(message))
#         if is_continuation:
#             logger.info("[INTENT] Continuation detected (regex)")
#             return {
#                 "intent_type": "continuation",
#                 "is_continuation": True,
#                 "is_greeting": False,
#                 "is_farewell": False,
#                 "is_presentation": False,
#                 "presentation_topic": None,
#                 "confidence": 1.0
#             }
        
#         # 5. Default: standard query
#         logger.info("[INTENT] Standard query")
#         return {
#             "intent_type": "query",
#             "is_continuation": False,
#             "is_greeting": False,
#             "is_farewell": False,
#             "is_presentation": False,
#             "presentation_topic": None,
#             "confidence": 1.0
#         }
    
#     def build_system_prompt(
#         self,
#         intent: Dict[str, Any],
#         has_context: bool = True,
#         is_presentation: bool = False
#     ) -> str:
#         """
#         Build system prompt based on intent, context availability, and source type.
        
#         Args:
#             intent: Intent dict from detect_intent
#             has_context: Whether RAG retrieved relevant context
#             is_presentation: Whether context is from presentation.json
        
#         Returns:
#             System prompt string
#         """
#         system_prompt = self.BASE_SYSTEM_PROMPT
        
#         # Internal note for presentation content (not shown to user)
#         if is_presentation:
#             system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
#             system_prompt += "\n🎓 PRESENTATION MODE:"
#             system_prompt += "\nThe content available is introductory workshop material."
#             system_prompt += "\n- Keep tone especially friendly and encouraging"
#             system_prompt += "\n- Focus on practical applications for students"
#             system_prompt += "\n- Use accessible, simple language"
#             system_prompt += "\n- Emphasize benefits and real-world relevance"
#             system_prompt += "\n- If asked for advanced details beyond scope, naturally acknowledge:"
#             system_prompt += "\n  'That gets into more advanced territory. Let me explain the core concept first...'"
#             system_prompt += "\n- NEVER say 'presentation' or 'introductory content' directly to the user\n"
#             system_prompt += "\n- The number of Key Points should ideally be from 9-10\n"
        
#         # Detailed mode for continuations
#         if intent.get('is_continuation', False):
#             system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
#             system_prompt += "\n🔥 DETAILED MODE ACTIVATED:"
#             system_prompt += "\nThe user wants MORE detailed information."
#             system_prompt += "\nProvide a thorough explanation:"
#             system_prompt += "\n- Write 4-6 paragraphs in <p> tags with proper HTML formatting"
#             system_prompt += "\n- Include concrete examples, analogies, and real-world applications"
#             system_prompt += "\n- Add practical tips, tools, or use cases"
#             system_prompt += "\n- Provide detailed key points in <ul><li> format—as many as fit the content"
#             system_prompt += "\n- Use <strong> for technical terms only (2-4 words max)"
#             system_prompt += "\n- Be comprehensive, engaging, and educational"
#             system_prompt += "\n- Teach deeply using ONLY the knowledge available to you\n"
        
#         # No context available
#         if not has_context:
#             system_prompt += "\n\n[INTERNAL NOTE - Not visible to user]"
#             system_prompt += "\n⚠️ NO INFORMATION AVAILABLE:"
#             system_prompt += "\nYou don't have knowledge to answer this specific query."
#             system_prompt += "\nRespond naturally:"
#             system_prompt += "\n'I don't have specific information about that. I can help with topics like [list 2-3 related AI/ML topics].'"
#             system_prompt += "\nBe brief and redirect to your areas of expertise. Don't over-apologize.\n"
        
#         logger.info(f"[PROMPT_BUILD] Intent: {intent.get('intent_type')}, Has context: {has_context}, Presentation: {is_presentation}, Continuation: {intent.get('is_continuation', False)}")
#         return system_prompt
    
#     def build_user_prompt(
#         self,
#         query: str,
#         context_chunks: List[str],
#         intent: Dict[str, Any],
#         is_presentation: bool = False
#     ) -> str:
#         """
#         Build user prompt with query and retrieved context.
#         Context is injected invisibly—LLM internalizes it as background knowledge.
        
#         Args:
#             query: User's question
#             context_chunks: Retrieved context from RAG
#             intent: Intent dict
#             is_presentation: Whether context is from presentation
        
#         Returns:
#             Formatted user prompt
#         """
#         if not context_chunks:
#             # No context available
#             user_prompt = f"""[No educational content available for this query]

# User Question: {query}

# ⚠️ You don't have information to answer this. Respond naturally that you don't have details about this specific topic, and suggest related AI/ML topics you can help with."""
#             return user_prompt
        
#         # Build hidden context section (LLM internalizes this as knowledge)
#         context_section = "[Educational content for reference - internalize as your expertise]:\n\n"
        
#         # Truncate each chunk to save tokens while preserving meaning
#         for idx, chunk in enumerate(context_chunks[:3], 1):  # Max 3 chunks
#             truncated_chunk = chunk[:800] + "..." if len(chunk) > 800 else chunk
#             context_section += f"{truncated_chunk}\n\n"
        
#         context_section += "---\n\n"
        
#         # Build final prompt
#         user_prompt = context_section
#         user_prompt += f"Student Question: {query}\n\n"
        
#         # Detect if this is a list-heavy query (e.g., careers)
#         is_list_query = any(keyword in query.lower() for keyword in ['careers', 'roles', 'jobs', 'list of']) or 'careers' in ''.join(context_chunks).lower()
        
#         if is_presentation or is_list_query:
#             user_prompt += """Present the content above naturally, focusing on lists if present.

# Format:
# <strong>Answer:</strong>
# <p>2-3 paragraphs introducing the topic.</p>

# <strong>Key Points:</strong>
# <ul>
# <li><strong>Item Name:</strong> Full description from content. Example: example text.</li>
# ... (repeat for EVERY item)
# </ul>

# Rules:
# 1. If the content includes a list (e.g., careers), include EVERY single item as a separate <li>.
# 2. Use exact titles, descriptions, and examples from the content—do not skip, merge, or add.
# 3. Count the items in the content and output that exact number of <li> tags.
# 4. For non-list topics, use 3-5 points as natural.
# 5. Complete the full list before ending.
# 6. HTML formatting only
# 7. Never mention sources"""
#             return user_prompt
        
#         # Instructions based on mode (continuation vs standard)
#         if intent.get('is_continuation', False):
#             user_prompt += """Provide detailed explanation:
# - Write 4-6 paragraphs in <p> tags
# - Include key points in <ul><li> with <strong> on terms—as many as fit the content.
# - Add examples and use cases
# - HTML formatting only
# - Never mention sources"""
#         else:
#             user_prompt += """Provide clear answer:
# - Write 2-3 paragraphs in <p> tags
# - Include key points in <ul><li> with <strong> on terms—as many as naturally fit (e.g., all from content for lists).
# - HTML formatting only
# - Never mention sources"""
        
#         return user_prompt

#     def build_greeting_response(self) -> str:
#         """Build a welcoming greeting response."""
#         return "👋 Hello! I'm <strong>AI Shine</strong>, your AI/ML educational assistant. Ask me anything about Artificial Intelligence, Machine Learning, or AI-powered education!"

#     def build_farewell_response(self) -> str:
#         """Build a warm farewell response for when the user says bye."""
#         return "👋 Goodbye! It was great chatting with you about AI and ML. Feel free to come back anytime for more learning!"


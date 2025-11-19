"""
Prompt Builder
Dynamically constructs system prompts with STRICT domain restriction and natural tone.
COMPLETE VERSION - Gemini-safe, no finish_reason=2 errors.
"""
import logging
from typing import Dict, Any, List

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

📝 RESPONSE FORMAT - STRICT HTML STRUCTURE:

<strong>Answer:</strong>

<p>First paragraph with clear explanation. Use <strong>key technical terms</strong> sparingly (2-4 words max per bold instance) for important concepts only.</p>

<p>Second paragraph with practical context or examples. Keep paragraphs focused—each should be 3-5 sentences.</p>

<p>Third paragraph (if needed) with deeper insight or real-world applications.</p>

<strong>Key Points:</strong>
<ul>
<li><strong>First concept:</strong> Clear, specific explanation</li>
<li><strong>Second concept:</strong> Practical application or detail</li>
<li><strong>Third concept:</strong> Real-world relevance</li>
<li><strong>Fourth concept:</strong> Additional important point </li>
<li><strong>Fifth concept:</strong> Additional important point </li>
<li><strong>Sixth concept:</strong> Additional important point </li>
<li><strong>Seventh concept:</strong> Additional important point </li>
<li><strong>Eighth concept:</strong> Additional important point </li>
<li><strong>Ninth concept:</strong> Additional important point (9-10 total)</li>

</ul>

🎨 FORMATTING RULES - MANDATORY:
1. ALWAYS use HTML: <p> for paragraphs, <strong> for bold, <ul><li> for lists
2. Use <strong> ONLY for critical technical terms (2-4 words maximum)
3. Each paragraph MUST be in <p></p> tags
4. Key Points MUST use <ul><li> structure and 9 points by default
5. Bold sparingly—only essential technical terms
6. Paragraphs should be 3-5 sentences each
7. NEVER use markdown (**, *, `) - ONLY HTML
8. NO plain text outside HTML tags
9. Concepts in Key Points should be <strong>

📏 RESPONSE LENGTH:

DEFAULT MODE (Standard Answer):
- 2-3 paragraphs in Answer section
- 9 key points with specifics
- Total: ~150-250 words
- Focus on clarity and directness

DETAILED MODE (When User Wants More):
Triggered by: "more detail", "elaborate", "tell me more", "explain further", "go deeper", "continue"
- 4-6 paragraphs in Answer section
- 9-12 detailed key points
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
You're an AI/ML expert teaching a student. The knowledge you share comes naturally from your expertise. Be helpful, accurate, and never make things up. If you don't know something specific, redirect to what you do know. Speak naturally and vary your explanations."""

    def __init__(self):
        pass
    
    def build_system_prompt(
        self,
        intent: Dict[str, Any],
        has_context: bool = True,
        is_presentation: bool = False
    ) -> str:
        """
        Build system prompt based on intent, context availability, and source type.
        
        Args:
            intent: Intent dict from IntentDetector
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
            system_prompt += "\n- Provide 9 detailed key points in <ul><li> format"
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
        
        # ✅ GEMINI-SAFE: Ultra-minimal presentation instruction
        # ✅ HYBRID: Gemini-safe but deterministic 9-item output
#         if is_presentation:
#             user_prompt += """Present the workshop content above using this exact structure:

# Write: <strong>Answer:</strong>
# Then: 2-3 intro paragraphs in <p> tags

# Write: <strong>Key Points:</strong>
# Then: List EVERY career/feature from above in <ul><li> format

# Format each item as:
# <li><strong>Career Name:</strong> description. Example: specific example.</li>

# Critical rules:
# 1. List all 9 careers in content as shown in Careers List (MUST list all 9)
# 2. Never skip items
# 3. Never add your own careers
# 4. Use only information from content above
# 5. Bold only the career name in each <li>

# Careers List (repeat for ALL items):
# <li><strong>AI Solution Architect:</strong> They build the 'brains' behind AI. Example: bridges gap between teams.</li>
# <li><strong>Data Scientist:</strong> Find patterns in data. Example: Netflix recommendations.</li>
# <li><strong>Robotics Engineer:</strong> Design robots. Example: NASA Mars exploration robots.</li>
# <li><strong>Healthcare Analyst:</strong> Use AI to detect diseases. Example: detect cancer from X-rays.</li>
# <li><strong>Cybersecurity Analyst:</strong> Use AI for protection. Example: detect fake emails.</li>
# <li><strong>AI Entrepreneur:</strong> Create AI products. Example: chatbot for rural schools.</li>
# <li><strong>AI Product Manager:</strong> End-to-end product development. Example: design and launch AI products.</li>
# <li><strong>Environmental AI Scientist:</strong> Solve environmental challenges. Example: predict floods via satellite.</li>
# </ul>
# [continue for remaining careers if available]"""
#             return user_prompt
        
#         # Instructions based on mode (continuation vs standard)
#         if intent.get('is_continuation', False):
#             user_prompt += """Provide detailed explanation:
# - Write 4-6 paragraphs in <p> tags
# - Include 5-7 key points in <ul><li> with <strong> on terms
# - Add examples and use cases
# - HTML formatting only
# - Never mention sources"""
#         else:
#             user_prompt += """Provide clear answer:
# - Write 2-3 paragraphs in <p> tags
# - Include 3-5 key points in <ul><li> with <strong> on terms
# - HTML formatting only
# - Never mention sources"""
        
#         return user_prompt

    
    # In prompt_builder.py, line ~270, replace the entire presentation block with:

        if is_presentation:
            user_prompt += """Present the content above naturally.

        Format:
        <strong>Answer:</strong>
        <p>Write 2-3 paragraphs introducing the topic</p>

        <strong>Key Points:</strong>
        <ul>
        <li><strong>Item Name:</strong> Full description. Example: example text.</li>
        <li><strong>Item Name:</strong> Full description. Example: example text.</li>
        ... continue for EVERY item in the content above
        </ul>

        Rules:
        1. Include EVERY career/feature/activity from the content above
        2. Do not skip any items - list them ALL
        3. Do not add items not in the content
        4. Use the exact titles and descriptions from above
        5. If content has 9 items, your output must have 9 <li> tags
        6. Count carefully before finishing

        DO NOT output anything until you've included every single item from the content."""
            return user_prompt
        # Instructions based on mode (continuation vs standard)
        if intent.get('is_continuation', False):
            user_prompt += """Provide detailed explanation:
- Write 4-6 paragraphs in <p> tags
- Include 5-7 key points in <ul><li> with <strong> on terms
- Add examples and use cases
- HTML formatting only
- Never mention sources"""
        else:
            user_prompt += """Provide clear answer:
- Write 2-3 paragraphs in <p> tags
- Include 3-5 key points in <ul><li> with <strong> on terms AND for career related query include 9 key points
- HTML formatting only
- Never mention sources"""
        
        return user_prompt

    def build_greeting_response(self) -> str:
        """Build a welcoming greeting response."""
        return "👋 Hello! I'm <strong>AI Shine</strong>, your AI/ML educational assistant. Ask me anything about Artificial Intelligence, Machine Learning, or AI-powered education!"





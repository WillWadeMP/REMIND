import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.claude_client import ClaudeClient
from src.concept_manager import ConceptManager
from src.utils import clean_text

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, concepts_dir: Path):
        self.concept_manager = ConceptManager(concepts_dir)
        self.claude = ClaudeClient()
        logger.info("New MemoryManager initialized using the dynamic concept graph system.")

    def classify_tone(self, statement: str) -> str:
        prompt = f"""
Classify the tone of the following statement as one of: literal, metaphorical, hypothetical, rhetorical, sarcastic, or unclear.
Statement:
"{statement}"
"""
        result = self.claude.complete(prompt, temperature=0, max_tokens=20).strip().lower()
        allowed = {"literal", "metaphorical", "hypothetical", "rhetorical", "sarcastic", "unclear"}
        return result if result in allowed else "unclear"

    def process_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        text = clean_text(text)
        now = datetime.utcnow().isoformat()
        memory_id = metadata.get("memory_id") if metadata else None

        # Extract keywords with Claude
        keyword_prompt = f"""
You are a smart memory indexing assistant. Your task is to extract up to 10 important keywords and bigrams from the following text:

"{text}"

Only return a list of keywords, one per line. No explanations. Focus on core nouns and noun phrases.
"""
        raw_keywords = self.claude.complete(keyword_prompt, temperature=0.3, max_tokens=150)
        candidate_concepts = [line.strip() for line in raw_keywords.splitlines() if line.strip()]

        updated_concepts = []

        for concept in candidate_concepts:
            node = self.concept_manager.get_concept(concept)
            node.add_tag(concept)

            # Co-occurrence
            for other in candidate_concepts:
                if other != concept:
                    node.relate_to(other, "co-occurs")

            # Summarization
            summary_prompt = f"""
You're updating a knowledge base of people, places, and concepts.
From the memory below, write a short, natural summary of what it reveals about the concept "{concept}". Focus on facts, traits, or events tied to it. Do not say “this memory shows...” or “only mentions...”, just write the knowledge as if you're updating a profile.
Memory:
"{text}"
"""
            summary = self.claude.complete(summary_prompt, temperature=0.3, max_tokens=150).strip()
            tone = self.classify_tone(summary)

            # Store structured summary
            new_entry = {
                "text": summary,
                "memory_id": memory_id,
                "date": now,
                "tone": tone,
            }

            existing_summaries = node.data["traits"].get("summary", [])
            existing_summaries.append(new_entry)
            node.data["traits"]["summary"] = existing_summaries

            if memory_id:
                node.link_memory(memory_id)
            node.add_trait("last_updated_memory", now)

            self.concept_manager.save_concept(node)
            updated_concepts.append(node.data["name"])

        logger.info(f"Processed memory into concept nodes: {updated_concepts}")
        return updated_concepts

    def retrieve_relevant_concepts(self, query: str) -> List[Dict[str, Any]]:
        keyword_prompt = f"""
Extract important keywords or bigrams from the following query:
"{query}"
Only return a list, one keyword or phrase per line.
"""
        raw_keywords = self.claude.complete(keyword_prompt, temperature=0.3, max_tokens=100)
        keywords = [line.strip() for line in raw_keywords.splitlines() if line.strip()]

        relevant_nodes = []
        seen_names = set()

        for keyword in keywords:
            nodes = self.concept_manager.search_concepts(keyword)
            for node in nodes:
                if node.data["name"] not in seen_names:
                    relevant_nodes.append(node.data)
                    seen_names.add(node.data["name"])

        logger.info(f"Retrieved {len(relevant_nodes)} relevant concept nodes for query: '{query}'")
        return relevant_nodes

    def generate_response(self, query: str) -> str:
        relevant_concepts = self.retrieve_relevant_concepts(query)
        context_parts = []
        new_info_parts = []

        freshness_threshold = datetime.utcnow() - timedelta(seconds=60)

        for concept in relevant_concepts:
            name = concept.get("name", "")
            ctype = concept.get("type", "unknown")
            tags = ", ".join(concept.get("tags", []))
            traits = concept.get("traits", {})
            summaries = traits.get("summary", [])

            literal = [s["text"] for s in summaries if s.get("tone") == "literal"]
            metaphor = [s["text"] for s in summaries if s.get("tone") == "metaphorical"]
            unclear = [s["text"] for s in summaries if s.get("tone") not in {"literal", "metaphorical"}]

            section = f"Concept: {name} (Type: {ctype})\nTags: {tags}\n"
            if literal:
                section += "Facts (literal):\n- " + "\n- ".join(literal) + "\n"
            if metaphor:
                section += "Theories (metaphorical):\n- " + "\n- ".join(metaphor) + "\n"
            if unclear:
                section += "Disputed/unclear:\n- " + "\n- ".join(unclear) + "\n"

            # Check freshness
            last_updated = traits.get("last_updated_memory", "")
            is_recent = False
            try:
                is_recent = datetime.fromisoformat(last_updated) > freshness_threshold
            except:
                pass

            if is_recent:
                new_info_parts.append(section)
            else:
                context_parts.append(section)

        memory_context = "".join([
            "MEMORY CONTEXT:\n" + "\n\n".join(context_parts) if context_parts else "",
            "\n\nNEW INFORMATION (recently learned):\n" + "\n\n".join(new_info_parts) if new_info_parts else ""
        ])

        prompt = f"""
You are Claude, a helpful AI assistant that uses a dynamic concept memory system.

You have access to a memory system that works by extracting *concepts* from past user input. Each memory is broken down into core ideas or concepts, and those are stored in a concept graph. When the user asks a question, your job is to look at these concepts (presented in context) and use them naturally in your answers.

If the same concept appears in multiple conversations with differing summaries, assume they may refer to different interpretations of the concept unless one is clearly overriding the other.

Speak naturally and clearly. Avoid robotic phrasing like “I cannot determine.”

{memory_context}

User Query: {query}

Please provide a helpful and informed response using this context.
"""
        response = self.claude.complete(prompt, temperature=0.7, max_tokens=1000)
        return response

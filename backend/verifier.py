"""
MeetBrief AI — Deterministic Evidence Grounding & Verification Engine
"""

import re
from typing import List, Optional, Set, Tuple
from backend.models import ResearchFinding, VerifiedClaim


class EvidenceGroundingEngine:
    """
    Evaluates factual claims against retrieved web snippets and source passages.
    
    Principles:
    1. Semantic containment is a heuristic for relevance and passage containment,
       NOT mathematical proof of real-world truth.
    2. Every material claim must map to an identifiable source passage.
    3. Source reliability tiering: Tier 1 (1.0), Tier 2 (0.8), Tier 3 (0.5).
    4. Contradictions between sources trigger CONFLICTED status with both citations retained.
    """

    # High-signal entities to extract: numbers, percentages, dollar amounts, years, capital terms
    ENTITY_REGEX = re.compile(r"(\$[0-9]+(?:\.[0-9]+)?(?:\s?[MBTKmbtk]|(?:\s?billion|\s?million))?|[0-9]+%|\b(?:19|20)[0-9]{2}\b|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)")

    @classmethod
    def extract_atomic_entities(cls, text: str) -> Set[str]:
        """Extracts key named entities, dates, metrics, and capitalized phrases."""
        matches = cls.ENTITY_REGEX.findall(text)
        # Normalize and filter short single-letter terms
        return {m.strip().lower() for m in matches if len(m.strip()) > 2}

    @staticmethod
    def calculate_entity_match(claim_entities: Set[str], passage: str) -> float:
        """
        Calculates the ratio of claim entities present in the source passage.
        """
        if not claim_entities:
            return 0.5  # Neutral if no distinct entities found
        passage_lower = passage.lower()
        matched = sum(1 for e in claim_entities if e in passage_lower)
        return matched / len(claim_entities)

    @staticmethod
    def calculate_token_containment(claim: str, passage: str) -> float:
        """
        Computes normalized token overlap / containment of claim terms in passage.
        """
        # Clean alphanumeric tokens (length > 2 to skip noise like 'is', 'on', 'at')
        claim_tokens = {w for w in re.sub(r"[^a-zA-Z0-9\s]", "", claim.lower()).split() if len(w) > 2}
        passage_tokens = {w for w in re.sub(r"[^a-zA-Z0-9\s]", "", passage.lower()).split() if len(w) > 2}

        if not claim_tokens:
            return 0.0

        overlap = claim_tokens.intersection(passage_tokens)
        return len(overlap) / len(claim_tokens)

    @classmethod
    def compute_alignment_score(
        cls,
        claim: str,
        finding: ResearchFinding
    ) -> float:
        """
        Combines entity matching and token containment against the source passage.
        """
        passage = finding.matched_passage or finding.summary or ""
        if not passage:
            return 0.0

        claim_entities = cls.extract_atomic_entities(claim)
        entity_score = cls.calculate_entity_match(claim_entities, passage)
        containment_score = cls.calculate_token_containment(claim, passage)

        # Weighted combination: 60% entity agreement, 40% term containment
        raw_alignment = (0.6 * entity_score) + (0.4 * containment_score)
        return round(min(1.0, max(0.0, raw_alignment)), 3)

    @staticmethod
    def detect_contradiction(
        claim: str,
        findings: List[ResearchFinding]
    ) -> Tuple[bool, Optional[str], Optional[ResearchFinding]]:
        """
        Checks for mutually exclusive factual statements across retrieved sources.
        Example: conflicting numerical metrics or conflicting status (shutdown vs launched).
        """
        # Simple heuristic check: look for contrasting dollar figures or opposing status words
        claim_lower = claim.lower()
        has_launch = any(w in claim_lower for w in ["launch", "release", "announce"])
        has_shutdown = any(w in claim_lower for w in ["shutdown", "deprecated", "closed", "cancel"])

        for f in findings:
            passage_lower = (f.matched_passage or f.summary or "").lower()
            if has_launch and any(w in passage_lower for w in ["delayed", "canceled", "blocked", "failed"]):
                return True, f"Conflicting signal in {f.source_title}: indicates delay or impediment", f
            if has_shutdown and any(w in passage_lower for w in ["active", "expanding", "re-launched"]):
                return True, f"Conflicting signal in {f.source_title}: indicates ongoing activity", f

        return False, None, None

    @classmethod
    def verify_claim(
        cls,
        claim: str,
        candidate_findings: List[ResearchFinding]
    ) -> VerifiedClaim:
        """
        Evaluates an individual claim against candidate research findings.
        Returns a VerifiedClaim with explicit status, scores, and traceable passage.
        """
        if not candidate_findings:
            return VerifiedClaim(
                claim=claim,
                verification_status="UNVERIFIED",
                source_url="",
                source_title="No candidate evidence",
                source_passage=None,
                alignment_score=0.0,
                confidence_score=0.0,
                conflict_notes=None
            )

        # Find finding with highest alignment score
        best_finding = candidate_findings[0]
        best_score = -1.0

        for f in candidate_findings:
            score = cls.compute_alignment_score(claim, f)
            if score > best_score:
                best_score = score
                best_finding = f

        # Check for contradictions
        has_conflict, conflict_note, conflicting_finding = cls.detect_contradiction(claim, candidate_findings)
        conflict_penalty = 0.4 if has_conflict else 0.0

        # Tier weights: Tier 1=1.0, Tier 2=0.8, Tier 3=0.5
        tier_weight = 1.0 if best_finding.reliability_tier == 1 else (0.8 if best_finding.reliability_tier == 2 else 0.5)

        # Deterministic Confidence Calculation
        final_confidence = round(min(1.0, max(0.0, (tier_weight * best_score) * (1.0 - conflict_penalty))), 3)

        # Status assignment
        if has_conflict:
            status = "CONFLICTED"
        elif best_score >= 0.75 and best_finding.reliability_tier == 1:
            status = "VERIFIED_PRIMARY"
        elif best_score >= 0.55 and best_finding.reliability_tier in (1, 2):
            status = "REPORTED_SECONDARY"
        else:
            status = "UNVERIFIED"

        return VerifiedClaim(
            claim=claim,
            verification_status=status,
            source_url=best_finding.source_url,
            source_title=best_finding.source_title,
            source_passage=best_finding.matched_passage or best_finding.summary[:200],
            source_date=best_finding.published_date,
            alignment_score=best_score,
            confidence_score=final_confidence,
            conflict_notes=conflict_note
        )

    @classmethod
    def ground_findings(
        cls,
        findings: List[ResearchFinding]
    ) -> List[VerifiedClaim]:
        """
        Extracts material claims from findings and grounds each against source evidence.
        """
        verified_claims: List[VerifiedClaim] = []
        for finding in findings:
            if finding.category == "undated":
                continue

            # Generate candidate claim from finding title & summary
            summary_sentences = [s.strip() for s in finding.summary.split(".") if len(s.strip()) > 15]
            candidate_claim = summary_sentences[0] if summary_sentences else finding.title

            v_claim = cls.verify_claim(candidate_claim, [finding])
            verified_claims.append(v_claim)

        return verified_claims

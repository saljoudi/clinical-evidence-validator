"""
Evidence Scoring Engine
"""
from typing import Dict, Any


class EvidenceScorer:
    """Calculate evidence quality scores based on SHACL validation results"""
    
    def calculate_integrity(self, validation_results: Dict[str, Any]) -> float:
        """FIX: Return simple pass rate - penalty logic was backwards"""
        parsed = validation_results.get("parsed_report", {})
        total = parsed.get("total_constraints", 10)
        passing = parsed.get("passing_constraints", 0)
        
        if total == 0:
            return 0.0
        
        return passing / total  # Simple, correct calculation
    
    def calculate_fairness(self, validation_results: Dict[str, Any]) -> float:
        """Calculate FAIR metadata score (0-1)"""
        parsed = validation_results.get("parsed_report", {})
        violations = parsed.get("violations", [])
        
        # Count FAIR-related violations
        fair_violations = [
            v for v in violations 
            if "license" in v.lower() or "identifier" in v.lower() or "version" in v.lower()
        ]
        
        # Max score if no FAIR violations
        return max(0.0, 1.0 - (len(fair_violations) * 0.33))
    
    def calculate_overall_score(self, integrity: float, fairness: float, fhir_compliance: float) -> float:
        """Calculate weighted overall score"""
        return 0.4 * integrity + 0.3 * fairness + 0.3 * fhir_compliance
    
    def generate_feedback(self, scores: Dict[str, float]) -> Dict[str, str]:
        """Generate textual feedback based on scores"""
        feedback = {}
        
        # Integrity feedback
        if scores["integrity"] >= 0.8:
            feedback["integrity"] = "Excellent statistical integrity. All constraints passed."
        elif scores["integrity"] >= 0.6:
            feedback["integrity"] = "Good statistical integrity. Minor issues detected."
        elif scores["integrity"] >= 0.4:
            feedback["integrity"] = "Fair statistical integrity. Some constraints failed."
        else:
            feedback["integrity"] = "Poor statistical integrity. Critical issues found."
        
        # FAIR feedback
        if scores["fairness"] >= 0.8:
            feedback["fairness"] = "FAIR principles fully met. Complete metadata."
        elif scores["fairness"] >= 0.6:
            feedback["fairness"] = "Good FAIR compliance. Minor metadata missing."
        elif scores["fairness"] >= 0.4:
            feedback["fairness"] = "Partial FAIR compliance. License/identifier/version needed."
        else:
            feedback["fairness"] = "Poor FAIR compliance. Essential metadata missing."
        
        # FHIR feedback
        if scores["fhir_compliance"] >= 0.8:
            feedback["fhir_compliance"] = "Full FHIR compliance. Valid structure."
        elif scores["fhir_compliance"] >= 0.6:
            feedback["fhir_compliance"] = "Good FHIR compliance. Minor validation issues."
        elif scores["fhir_compliance"] >= 0.4:
            feedback["fhir_compliance"] = "Partial FHIR compliance. Some required fields missing."
        else:
            feedback["fhir_compliance"] = "Poor FHIR compliance. Invalid structure."
        
        # Overall
        overall = scores["overall"]
        if overall >= 0.8:
            feedback["overall"] = "High-quality evidence. Ready for clinical use."
        elif overall >= 0.6:
            feedback["overall"] = "Moderate-quality evidence. Review recommended."
        elif overall >= 0.4:
            feedback["overall"] = "Low-quality evidence. Significant issues need addressing."
        else:
            feedback["overall"] = "Evidence not suitable for clinical use. Major revisions required."
        

        return feedback

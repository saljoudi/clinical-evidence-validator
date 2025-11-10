"""
FHIR Resource Validator
"""
import json
from typing import List, Dict, Any
from fhir.resources.evidence import Evidence
from fhir.resources.fhirtypes import EvidenceVariableType
import pydantic


class FHIRValidator:
    """Validates FHIR Evidence resources for compliance"""
    
    def __init__(self):
        self.required_fields = [
            "status",
            "statisticalTest",
            "sampleSize",
            "pValue"
        ]
    
    def validate_fhir_resources(self, resources: List[Dict[str, Any]]) -> float:
        """Validate FHIR Evidence resources and return compliance score (0-1)"""
        if not resources:
            return 0.0
        
        scores = []
        for resource in resources:
            score = self._validate_single_resource(resource)
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _validate_single_resource(self, resource: Dict[str, Any]) -> float:
        """Validate a single FHIR Evidence resource"""
        try:
            # Try to create FHIR Evidence object
            evidence = Evidence.parse_obj(resource)
            
            # Check required fields
            score = 0.0
            checks = 0
            
            if evidence.status:
                score += 1.0
            checks += 1
            
            if evidence.statisticalTest and len(evidence.statisticalTest) > 0:
                score += 1.0
            checks += 1
            
            if evidence.sampleSize and evidence.sampleSize.value:
                score += 1.0
            checks += 1
            
            if evidence.pValue and evidence.pValue.value is not None:
                # Check p-value is valid
                if 0 <= evidence.pValue.value <= 1:
                    score += 1.0
            checks += 1
            
            # Validate resource type
            if evidence.resourceType == "Evidence":
                score += 1.0
            checks += 1
            
            return score / checks if checks > 0 else 0.0
            
        except pydantic.ValidationError as e:
            print(f"FHIR validation error: {e}")
            return 0.0
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 0.0
    
    def validate_json_structure(self, json_data: str) -> Dict[str, Any]:
        """Validate JSON structure against FHIR schema"""
        try:
            data = json.loads(json_data)
            
            if isinstance(data, list):
                resources = data
            else:
                resources = [data]
            
            results = []
            for resource in resources:
                try:
                    Evidence.parse_obj(resource)
                    results.append({"valid": True, "errors": []})
                except pydantic.ValidationError as e:
                    errors = [{"field": err['loc'], "msg": err['msg']} for err in e.errors()]
                    results.append({"valid": False, "errors": errors})
            
            return {
                "valid": all(r["valid"] for r in results),
                "results": results,
                "resourceCount": len(resources)
            }
        
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON: {str(e)}",
                "results": []
            }
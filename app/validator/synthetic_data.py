"""
Synthetic Clinical Evidence Data Generator
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Dict, Any
import uuid


class SyntheticDataGenerator:
    """Generate synthetic clinical trial data and FHIR Evidence resources"""
    
    def generate_dataset(
        self, 
        n_samples: int = 100, 
        evidence_type: str = "t-test",
        seed: int = None
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Generate synthetic dataset based on evidence type"""
        
        if seed is not None:
            np.random.seed(seed)
        
        if evidence_type == "t-test":
            return self._generate_ttest_data(n_samples)
        elif evidence_type == "chi-square":
            return self._generate_chisquare_data(n_samples)
        elif evidence_type == "logistic-regression":
            return self._generate_logistic_data(n_samples)
        elif evidence_type == "kaplan-meier":
            return self._generate_survival_data(n_samples)
        else:
            raise ValueError(f"Unsupported evidence type: {evidence_type}")
    
    def _generate_ttest_data(self, n_samples: int) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generate t-test data: two groups with continuous outcome"""
        n_per_group = n_samples // 2
        
        # Group 1: treatment
        group1 = np.random.normal(loc=75, scale=15, size=n_per_group)
        
        # Group 2: control
        group2 = np.random.normal(loc=65, scale=15, size=n_per_group)
        
        df = pd.DataFrame({
            'patient_id': range(1, n_samples + 1),
            'group': ['treatment'] * n_per_group + ['control'] * n_per_group,
            'outcome': np.concatenate([group1, group2])
        })
        
        # Calculate statistics
        t_stat, p_value = stats.ttest_ind(group1, group2)
        
        # Create FHIR Evidence
        fhir_resource = {
            "resourceType": "Evidence",
            "id": str(uuid.uuid4()),
            "status": "draft",
            "description": f"t-test: t={t_stat:.3f}, p={p_value:.3f}",
            "statistic": [{
                "numberOfParticipants": n_samples,
                "valueNumber": float(t_stat),
                "unitOfMeasure": {
                    "coding": [{
                        "system": "http://unitsofmeasure.org",
                        "code": "t",
                        "display": "t-statistic"
                    }]
                }
            }],
            "pValue": {
                "value": float(p_value),
                "unit": "p-value"
            },
            "license": "CC-BY-4.0",
            "identifier": [{
                "system": "https://doi.org",
                "value": f"10.1234/syn.{uuid.uuid4()}"
            }],
            "version": "1.0.0"
        }        
        return df, [fhir_resource]
    
    def _generate_chisquare_data(self, n_samples: int) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generate chi-square test data: categorical variables"""
        # Treatment vs Control, Outcome: Improved/Not Improved
        contingency = np.array([
            [30, 20],  # Treatment: 30 improved, 20 not
            [20, 30]   # Control: 20 improved, 30 not
        ])
        
        # Generate patient data
        data = []
        for i in range(n_samples):
            if i < n_samples // 2:
                group = 'treatment'
                # 60% improvement rate
                improved = np.random.choice(['Yes', 'No'], p=[0.6, 0.4])
            else:
                group = 'control'
                # 40% improvement rate
                improved = np.random.choice(['Yes', 'No'], p=[0.4, 0.6])
            
            data.append({
                'patient_id': i + 1,
                'group': group,
                'outcome': improved
            })
        
        df = pd.DataFrame(data)
        
        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        fhir_resource = {
            "resourceType": "Evidence",
            "id": str(uuid.uuid4()),
            "status": "draft",
            "statisticalTest": {
                "coding": [{
                    "system": "http://purl.obolibrary.org/obo/stato.owl",
                    "code": "chi-square",
                    "display": "Chi-square test"
                }]
            },
            "statistic": [{
                "type": "chi-square",
                "value": float(chi2)
            }],
            "pValue": {
                "value": float(p_value)
            },
            "variable": [
                {"name": "group", "value": "treatment_vs_control"},
                {"name": "outcome", "value": "improvement"}
            ],
            "sampleSize": {
                "value": n_samples
            },
            "license": "CC-BY-4.0",
            "identifier": [{
                "system": "https://doi.org",
                "value": f"https://doi.org/10.1234/syn.{uuid.uuid4()}"
            }],
            "version": "1.0.0"
        }
        
        return df, [fhir_resource]
    
    def _generate_logistic_data(self, n_samples: int) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generate logistic regression data"""
        # Features: age, treatment (0/1), comorbidities
        age = np.random.normal(60, 10, n_samples)
        treatment = np.random.binomial(1, 0.5, n_samples)
        
        # Log odds
        log_odds = -2 + 0.05 * age + 1.2 * treatment
        p = 1 / (1 + np.exp(-log_odds))
        
        outcome = np.random.binomial(1, p, n_samples)
        
        df = pd.DataFrame({
            'patient_id': range(1, n_samples + 1),
            'age': age,
            'treatment': treatment,
            'outcome': outcome
        })
        
        fhir_resource = {
            "resourceType": "Evidence",
            "id": str(uuid.uuid4()),
            "status": "draft",
            "statisticalTest": {
                "coding": [{
                    "system": "http://purl.obolibrary.org/obo/stato.owl",
                    "code": "logistic-regression",
                    "display": "Logistic Regression"
                }]
            },
            "outcome": {
                "value": "binary_outcome"
            },
            "coefficient": [0.05, 1.2],  # Age and treatment coefficients
            "oddsRatio": [1.05, 3.32],   # exp(coeff)
            "variable": ["age", "treatment"],
            "sampleSize": {
                "value": n_samples
            },
            "license": "CC-BY-4.0",
            "identifier": [{
                "system": "https://doi.org",
                "value": f"https://doi.org/10.1234/syn.{uuid.uuid4()}"
            }],
            "version": "1.0.0"
        }
        
        return df, [fhir_resource]
    
    def _generate_survival_data(self, n_samples: int) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generate Kaplan-Meier survival data"""
        # Time to event in months
        time_to_event = np.random.exponential(12, n_samples)
        
        # Censoring indicator (1=event, 0=censored)
        event_status = np.random.binomial(1, 0.7, n_samples)
        
        # Group: treatment vs control
        group = np.random.choice(['treatment', 'control'], n_samples)
        
        df = pd.DataFrame({
            'patient_id': range(1, n_samples + 1),
            'group': group,
            'time_to_event': time_to_event,
            'event_status': event_status
        })
        
        fhir_resource = {
            "resourceType": "Evidence",
            "id": str(uuid.uuid4()),
            "status": "draft",
            "statisticalTest": {
                "coding": [{
                    "system": "http://purl.obolibrary.org/obo/stato.owl",
                    "code": "kaplan-meier",
                    "display": "Kaplan-Meier Survival Analysis"
                }]
            },
            "timeToEvent": time_to_event.tolist(),
            "eventStatus": event_status.tolist(),
            "variable": ["treatment", "control"],
            "sampleSize": {
                "value": n_samples
            },
            "license": "CC-BY-4.0",
            "identifier": [{
                "system": "https://doi.org",
                "value": f"https://doi.org/10.1234/syn.{uuid.uuid4()}"
            }],
            "version": "1.0.0"
        }
        
        return df, [fhir_resource]
    
    def csv_to_fhir(self, df: pd.DataFrame, evidence_type: str) -> List[Dict[str, Any]]:
        """Convert CSV to FHIR Evidence resources (simplified)"""
        # This is a simplified conversion - in practice, map columns to FHIR fields
        
        if evidence_type == "t-test":
            # Assume two groups: 'group' and 'outcome' columns
            groups = df['group'].unique()
            if len(groups) == 2:
                group1 = df[df['group'] == groups[0]]['outcome']
                group2 = df[df['group'] == groups[1]]['outcome']
                t_stat, p_value = stats.ttest_ind(group1, group2)
                
                return [{
                    "resourceType": "Evidence",
                    "id": str(uuid.uuid4()),
                    "status": "draft",
                    "statisticalTest": {
                        "coding": [{
                            "system": "http://purl.obolibrary.org/obo/stato.owl",
                            "code": "t-test",
                            "display": "Student's t-test"
                        }]
                    },
                    "statistic": [{"type": "t-value", "value": float(t_stat)}],
                    "pValue": {"value": float(p_value)},
                    "variable": [{"name": "group", "value": str(g)} for g in groups],
                    "sampleSize": {"value": len(df)},
                    "license": "CC-BY-4.0",
                    "identifier": [{"system": "https://doi.org", "value": f"https://doi.org/10.1234/csv.{uuid.uuid4()}"}],
                    "version": "1.0"
                }]
        
        # Default fallback
        return [{
            "resourceType": "Evidence",
            "id": str(uuid.uuid4()),
            "status": "draft",
            "sampleSize": {"value": len(df)},
            "license": "CC-BY-4.0",
            "identifier": [{"system": "https://doi.org", "value": f"https://doi.org/10.1234/csv.{uuid.uuid4()}"}],
            "version": "1.0"

        }]

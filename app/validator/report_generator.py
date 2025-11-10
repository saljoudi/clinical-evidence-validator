"""
Report Generator - PDF, JSON, RDF outputs
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ReportGenerator:
    """Generate validation reports in multiple formats"""
    
    def __init__(self):
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_pdf(self, task_id: str, results: Dict[str, Any]) -> str:
        """Generate PDF validation report"""
        filename = self.output_dir / f"{task_id}.pdf"
        
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("Clinical Evidence Validation Report", title_style))
        story.append(Paragraph(f"Task ID: {task_id}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        scores = results["scores"]
        story.append(Paragraph(f"Overall Quality Score: {scores['overall']:.2f}/1.00", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        # Scores Table
        data = [
            ["Metric", "Score", "Weight"],
            ["Statistical Integrity", f"{scores['integrity']:.2f}", "40%"],
            ["FAIR Metadata", f"{scores['fairness']:.2f}", "30%"],
            ["FHIR Compliance", f"{scores['fhir_compliance']:.2f}", "30%"],
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Details
        story.append(Paragraph("Validation Details", styles['Heading2']))
        validation = results["validation_results"]
        story.append(Paragraph(f"SHACL Conformance: {'PASS' if validation['conforms'] else 'FAIL'}", styles['Normal']))
        story.append(Paragraph(f"Constraints Passing: {validation['passing_constraints']}/{validation['total_constraints']}", styles['Normal']))
        story.append(Paragraph(f"Violations: {validation['violations']}", styles['Normal']))
        
        # Evidence Type
        story.append(Spacer(1, 20))
        story.append(Paragraph("Evidence Characteristics", styles['Heading2']))
        story.append(Paragraph(f"Type: {results.get('evidence_type', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"Sample Size: {len(results.get('original_data', []))}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return str(filename)
    
    def generate_rdf(self, task_id: str, results: Dict[str, Any]) -> str:
        """Generate RDF/Turtle validation report"""
        filename = self.output_dir / f"{task_id}.ttl"
        
        g = Graph()
        OCEV = rdflib.Namespace("http://example.org/ocev/")
        
        # Create validation result node
        validation_uri = OCEV[f"validation/{task_id}"]
        g.add((validation_uri, rdflib.RDF.type, OCEV.ValidationResult))
        
        # Add scores
        scores = results["scores"]
        g.add((validation_uri, OCEV.overallScore, Literal(scores["overall"])))
        g.add((validation_uri, OCEV.integrityScore, Literal(scores["integrity"])))
        g.add((validation_uri, OCEV.fairnessScore, Literal(scores["fairness"])))
        g.add((validation_uri, OCEV.fhirScore, Literal(scores["fhir_compliance"])))
        
        # Add validation details
        validation_results = results["validation_results"]
        g.add((validation_uri, OCEV.conforms, Literal(validation_results["conforms"])))
        g.add((validation_uri, OCEV.constraintsPassed, Literal(validation_results["passing_constraints"])))
        g.add((validation_uri, OCEV.constraintsTotal, Literal(validation_results["total_constraints"])))
        
        # Serialize to TTL
        g.serialize(str(filename), format="turtle")
        return str(filename)
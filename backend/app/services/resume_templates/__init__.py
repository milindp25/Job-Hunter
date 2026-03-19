from __future__ import annotations

from app.services.resume_templates.base import ResumeData, ResumeTemplate, TemplateRegistry
from app.services.resume_templates.classic import ClassicTemplate
from app.services.resume_templates.minimal import MinimalTemplate
from app.services.resume_templates.modern import ModernTemplate

# Auto-register all templates
TemplateRegistry.register(ClassicTemplate())
TemplateRegistry.register(ModernTemplate())
TemplateRegistry.register(MinimalTemplate())

__all__ = [
    "ClassicTemplate",
    "MinimalTemplate",
    "ModernTemplate",
    "ResumeData",
    "ResumeTemplate",
    "TemplateRegistry",
]
